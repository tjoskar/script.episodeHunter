"""
Sync watched Movies/TV shows to Episodehunter
"""

import copy
from resources.exceptions import UserAbortExceptions, ConnectionExceptions, SettingsExceptions
from resources.lib import xbmc_helper
from resources.lib import helper
from resources.lib import sync
from resources.lib.gui import dialog
from resources.model import series_model


class Series(sync.Sync):
    """ Two way sync between EH and xbmc"""

    def __init__(self, connection):
        super(Series, self).__init__(connection)
        self.progress = None
        self.upstream_sync = []
        self.downstream_sync = []
        self.eh_watched_series = None
        self.xbmc_series = []

    def sync(self):
        self.create_progress(helper.language(32021))  # "Checking XBMC Database for new watched movies"
        try:
            self.get_series()
            self.get_series_to_sync_upstream()
            self.get_series_to_sync_downstream()
            self._sync()
        except UserAbortExceptions:
            dialog.create_ok(helper.language(32022))  # "Progress Aborted"
        except ConnectionExceptions as error:
            self.create_error_dialog(helper.language(32018), error.value)  # "Error"
        except SettingsExceptions as error:
            self.create_error_dialog(helper.language(32018), error.value)  # "Error"
        except SystemExit:
            pass
        except Exception, error:
            self.create_error_dialog(helper.language(32018), error.message)  # "Error"

        self.quit()

    def _sync(self):
        num_sync_upstream = len(self.upstream_sync)
        num_sync_downstream = len(self.downstream_sync)

        if num_sync_upstream > 0 and self.ask_user_yes_or_no(str(num_sync_upstream) + " " + helper.language(32023)):  # 'Movies will be added as watched on EpisodeHunter'
            self.progress_update(50, helper.language(32044))  # "Uploading movies to EpisodeHunter"
            # self.connection.set_shows_watched(self.upstream_sync)
            self.create_ok_dialog(helper.language(32040))  # "Movie successfully updated at EpisodeHunter"

        if num_sync_downstream > 0 and self.ask_user_yes_or_no(str(num_sync_downstream) + " " + helper.language(32047)):  # 'Movies will be marked as watched in xbmc'
            self.progress_update(75, helper.language(32048))  # "Setting movies as seen in xbmc"
            xbmc_helper.set_movies_as_watched(self.downstream_sync)

    def get_series_to_sync_upstream(self):
        xbmc_series = copy.copy(self.xbmc_series)
        num_series = len(xbmc_series)
        self.upstream_sync = []
        for i, tvdb_id in enumerate(xbmc_series.keys()):
            show = xbmc_series[tvdb_id]
            assert isinstance(show, series_model.Series)
            self.progress.update(50 / num_series * i)
            if self.is_canceled():
                break
            if show.plays <= 0:
                del xbmc_series[tvdb_id]
                continue
            show.episodes = [e for e in show.episodes if not self.episode_set_as_seen_on_eh(show.tvdb_id, e.season, e.episode)]
            self.upstream_sync.append(show)

    def get_series_to_sync_downstream(self):
        xbmc_series = copy.copy(self.xbmc_series)
        num_series = len(xbmc_series)
        self.downstream_sync = []
        for i, tvdb_id in enumerate(xbmc_series.keys()):
            show = xbmc_series[tvdb_id]
            assert isinstance(show, series_model.Series)
            self.progress.update(50 / num_series * i + 50)
            if self.is_canceled():
                break
            if show.plays > 0:
                del xbmc_series[tvdb_id]
                continue
            show.episodes = [e for e in show.episodes if self.episode_set_as_seen_on_eh(show.tvdb_id, e.season, e.episode)]
            self.downstream_sync.append(show)

    def episode_set_as_seen_on_eh(self, series_id, season, episode):
        """
        Check if a movie has been set as watched on EH
        :rtype : bool
        """
        series_id = str(series_id)
        season = str(season)
        episode = int(episode)
        if series_id not in self.eh_watched_series:
            return False
        if season not in self.eh_watched_series[series_id]:
            return False
        if episode not in self.eh_watched_series[series_id][season]:
            return False

        return True

    def get_series(self):
        self.get_series_from_eh()
        self.get_series_from_xbmc()

    def get_series_from_eh(self):
        eh_watched_series = self.connection.get_watched_shows()
        self.eh_watched_series = {}
        for k, v in eh_watched_series.iteritems():
            self.eh_watched_series[k] = {}
            for s in v['seasons']:
                self.eh_watched_series[k][s['season']] = s['episodes']

    def get_series_from_xbmc(self):
        xbmc_series = xbmc_helper.get_tv_shows_from_xbmc()

        for tvshow in xbmc_series:
            seasons = xbmc_helper.get_seasons_from_xbmc(tvshow)
            episodes = [xbmc_helper.get_episodes_from_xbmc(tvshow, season['season']) for season in seasons]
            if series_criteria(tvshow, episodes):
                continue
            self.xbmc_series.append(series_model.create_from_xbmc(tvshow, episodes))


def series_criteria(tvshow, episodes):
    """
    Determine if a shows meets the criteria
    :rtype : bool
    """
    if 'title' not in tvshow:
        return False

    if 'imdbnumber' not in tvshow:
        return False

    try:
        if 'year' not in tvshow or int(tvshow['year']) <= 0:
            return False
    except ValueError:
        return False

    if 'playcount' not in movie:
        return False

    if not all(['season' in e and 'episode' in e and 'playcount' in e for e in episodes]):
        return False

    return True