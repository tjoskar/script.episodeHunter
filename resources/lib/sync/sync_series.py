"""
Sync watched TV episodes to Episodehunter
"""

import sync
from resources.exceptions import UserAbortExceptions, ConnectionExceptions, SettingsExceptions
from resources.lib import xbmc_repository
from resources.lib import helper
from resources.lib.gui import dialog


class Series(sync.Sync):
    """ Two way sync between EH and xbmc"""

    def __init__(self, connection):
        super(Series, self).__init__(connection)
        self.eh_watched_series = []
        self.total_sync_episodes = 0

    def sync(self):
        helper.debug("Start syncing tv shows")
        self.create_progress(helper.language(32051))  # "Comparing XBMC database with episodehunter.tv"
        try:
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
        self.get_series_from_eh()
        self.sync_upstream()
        self.sync_downstream()

        if self.total_sync_episodes == 0:
            dialog.create_ok(helper.language(32050)) # "Your library is up to date. Nothing to sync"
        else:
            dialog.create_ok(helper.language(32053).format(self.total_sync_episodes)) # "{0} number of episodes has been synchronized"


    def sync_upstream(self):
        num = xbmc_repository.number_watched_shows()
        if num <= 0:
            return

        for i, show in enumerate(self.shows_to_sync_upstream()):
            self.check_if_canceled()
            self.progress_update(100*((i+1)/num), helper.language(32043), show['title']) # "Uploading shows to episodehunter.tv"
            self.connection.set_show_as_watched(show)
            self.total_sync_episodes = self.total_sync_episodes + len(show['episodes'])


    def sync_downstream(self):
        num = xbmc_repository.number_unwatched_shows()
        if num <= 0:
            return

        for i, show in enumerate(self.shows_to_sync_downstream()):
            self.check_if_canceled()
            self.progress_update(100*((i+1)/num), helper.language(32052), show['title']) # "Setting episodes as seen in xbmc"
            xbmc_repository.set_episodes_as_watched(show['episodes'])
            self.total_sync_episodes = self.total_sync_episodes + len(show['episodes'])


    def shows_to_sync_upstream(self):
        for xbmc_show in xbmc_repository.watched_shows():
            episodes = [
                e for e in xbmc_repository.watched_episodes(xbmc_show) or []
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


    def shows_to_sync_downstream(self):
        for xbmc_show in xbmc_repository.unwatched_shows():
            episodes = [
                e['episodeid'] for e in xbmc_repository.unwatched_episodes(xbmc_show) or []
                if self.is_marked_as_watched_on_eh(xbmc_show['imdbnumber'], e['season'], e['episode'])
            ]
            if not episodes:
                continue
            yield {
                'title': xbmc_show['title'],
                'episodes': episodes
            }


    def is_marked_as_watched_on_eh(self, series_id, season, episode):
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
