"""
Sync watched TV episodes to Episodehunter
"""

import copy
import sync
from resources.exceptions import UserAbortExceptions, ConnectionExceptions, SettingsExceptions
from resources.lib import xbmc_helper
from resources.lib import helper
from resources.lib.gui import dialog
from resources.model import series_model


class Series(sync.Sync):
    """ Two way sync between EH and xbmc"""

    def __init__(self, connection):
        super(Series, self).__init__(connection)
        self.progress = None
        self.upstream_sync = []
        self.downstream_sync = []
        self.eh_watched_series = []
        self.xbmc_series = []

    def sync(self):
        helper.debug("Start syncing tv shows")
        self.create_progress(helper.language(32051))  # "Comparing XBMC database with episodehunter.tv"
        try:
            self.get_series()
            self.get_series_to_sync_upstream()
            self.get_series_to_sync_downstream()
            self._sync()
        except UserAbortExceptions:
            dialog.create_ok(helper.language(32022))  # "Progress Aborted"
        except ConnectionExceptions as error:
            self.create_error_dialog(error.value)
        except SettingsExceptions as error:
            self.create_error_dialog(error.value)
        except SystemExit:
            pass

        helper.debug("The synchronize is complete")
        self.quit()

    def _sync(self):
        num_sync_upstream = sum(len(e.episodes) for e in self.upstream_sync)
        num_sync_downstream = sum(len(e.episodes) for e in self.downstream_sync)

        if num_sync_upstream > 0 and self.ask_user_yes_or_no(str(num_sync_upstream) + " " + helper.language(32031)):  # 'episodes will be marked as watched on episodehunter.tv'
            self.progress_update(50, helper.language(32043))  # "Uploading shows to episodehunter.tv"
            self.connection.set_shows_watched(self.upstream_sync)

        if num_sync_downstream > 0 and self.ask_user_yes_or_no(str(num_sync_downstream) + " " + helper.language(32049)):  # 'episode will be marked as watched in xbmc':
            self.progress_update(75, helper.language(32052))  # "Setting episodes as seen in xbmc"
            xbmc_helper.set_series_as_watched(self.downstream_sync)

        if num_sync_upstream == 0 and num_sync_downstream == 0:
            dialog.create_ok(helper.language(32050))


    def sync_upstream(self):
        for show in self.shows_to_sync_upstream():
            # Incleace progress, like a ln-function. self.progress.update(50 / num_series * i)
            self.check_if_canceled()
            self.connection.set_show_as_watched(show)


    def shows_to_sync_upstream(self):
        for xbmc_show in xbmc_helper.watched_shows():
            episodes = [
                e for e in xbmc_helper.get_watched_episodes(xbmc_show) or []
                if not self.is_marked_as_watched_on_eh(xbmc_show['imdbnumber'], e['season'], e['episode'])
            ]
            if not episodes:
                continue
            yield {
                'tvdb_id': xbmc_show['imdbnumber'],
                'title': xbmc_show['title'],
                'year': xbmc_show['year'],
                'episodes': episodes
            }


    def get_series_to_sync_downstream(self):
        xbmc_series = copy.deepcopy(self.xbmc_series)
        num_series = len(xbmc_series)
        self.downstream_sync = []
        for i, show in enumerate(xbmc_series):
            assert isinstance(show, series_model.Series)
            self.progress.update(50 / num_series * i + 50)
            if self.is_canceled():
                break
            show.episodes = [
                e for e in show.episodes
                if self.is_marked_as_watched_on_eh(show.tvdb_id, e.season, e.episode) and e.plays == 0
            ]
            if len(show.episodes) == 0:
                continue
            self.downstream_sync.append(show)

    def is_marked_as_watched_on_eh(self, series_id, season, episode):
        """
        Check if an episode has been set as watched on EH
        :rtype : bool
        """
        series_id = int(series_id)
        season = int(season)
        episode = int(episode)
        if series_id not in self.eh_watched_series:
            return False
        if season not in self.eh_watched_series[series_id]:
            return False
        if episode not in self.eh_watched_series[series_id][season]:
            return False

        return True

    def get_series_from_eh(self):
        eh_watched_series = self.connection.get_watched_shows()
        self.eh_watched_series = {}
        for k, v in eh_watched_series.iteritems():
            k = int(k)
            self.eh_watched_series[k] = {}
            for s in v['seasons']:
                self.eh_watched_series[k][int(s['season'])] = s['episodes']


    def watched_shows_in_xbmc(self):
        watched_shows = xbmc_helper.watched_shows()
        for show in watched_shows:
            episodes = [xbmc_helper.get_watched_episodes(show, season) for season in xbmc_helper.get_watched_seasons(show)]
            yield series_model.create_from_xbmc(show, episodes)
