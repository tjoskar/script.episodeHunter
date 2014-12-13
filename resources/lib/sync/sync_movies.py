from resources.lib.sync import Sync
from resources.lib import helper
from resources.model import movie_model
from resources.lib.gui import dialog
from resources.lib import xbmc_helper
from resources.exceptions import ConnectionExceptions, UserAbortExceptions, SettingsExceptions


class Movies(Sync):
    """
    Sync class
    Two-way sync between xbmc and EH
    """

    def __init__(self, connection):
        super(Movies, self).__init__()
        self.connection = connection
        self.progress = None
        self.upstream_sync = []
        self.downstream_sync = []
        self.eh_watched_movies = None
        self.xbmc_watched_movies = None

    def sync(self):
        self.create_progress(helper.language(32021))  # "Checking XBMC Database for new watched movies"
        try:
            self.get_watched_movies()
            self.get_movies_to_sync_upstream()
            self.get_movies_to_sync_downstream()
            self.__sync()
        except UserAbortExceptions:
            dialog.create_ok(helper.language(32022))  # "Progress Aborted"
        except ConnectionExceptions as error:
            self.create_error_dialog(helper.language(32018), error.value)  # "Error"
        except SettingsExceptions as error:
            self.create_error_dialog(helper.language(32018), error.value)  # "Error"
        except SystemExit:
            pass

        self.quit()

    def __sync(self):
        num_movies_to_sync = len(self.upstream_sync)

        if num_movies_to_sync > 0 and self.ask_user_yes_or_no(str(num_movies_to_sync) + " " + helper.language(32023)):  # 'Movies will be added as watched on EpisodeHunter'
            self.progress_update(50, helper.language(32044))  # "Uploading movies to EpisodeHunter"
            self.connection.set_movies_watched(self.upstream_sync)
            self.create_ok_dialog(helper.language(32040))  # "Movie successfully updated at EpisodeHunter"

    def get_movies_to_sync_upstream(self):
        num_movies = len(self.xbmc_watched_movies)
        self.upstream_sync = []
        for i, m in enumerate(self.xbmc_watched_movies):
            if self.is_canceled():
                break
            self.progress.update(100 / num_movies * i)
            if not movie_criteria(m):
                continue
            if self.movie_already_synced(m['imdbnumber']):
                continue
            self.upstream_sync.append(movie_model.create_from_xbmc(m))

    def get_movies_to_sync_downstream(self):
        pass

    def movie_already_synced(self, imdb):
        for movie in self.eh_watched_movies:
            if imdb == movie['imdb_id']:
                return True
        return False

    def get_watched_movies(self):
        self.eh_watched_movies = self.connection.get_watched_movies()
        self.xbmc_watched_movies = xbmc_helper.get_movies_from_xbmc()


def movie_criteria(movie):
    if 'imdbnumber' not in movie:
        helper.debug("Skipping a movie - no IMDb ID was found")
        return False

    if 'title' not in movie and 'originaltitle' not in movie:
        helper.debug("Skipping a movie - title not found")
        return False

    try:
        if 'year' not in movie or int(movie['year']) <= 0:
            helper.debug("Skipping a movie - year not found")
            return False
    except ValueError, error:
        helper.debug(error)

    try:
        if 'playcount' not in movie or int(movie['playcount']) <= 0:
            return False
    except ValueError, error:
        helper.debug(error)

    return True
