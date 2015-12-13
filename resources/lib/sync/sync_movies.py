from resources.lib.sync import Sync
from resources.lib import helper
from resources.lib.gui import dialog
from resources.lib import xbmc_repository
from resources.exceptions import ConnectionExceptions, UserAbortExceptions, SettingsExceptions


class Movies(Sync):
    """
    Sync class
    Two-way sync between xbmc and EH
    """

    def __init__(self, connection, xbmc=xbmc_repository):
        super(Movies, self).__init__(connection)
        self.eh_watched_movies = None
        self.total_sync_movies = 0
        self.xbmc = xbmc

    def sync(self):
        helper.debug("Start syncing movies")
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
        self.get_movies_from_eh()
        self.sync_upstream()
        self.sync_downstream()

        if self.total_sync_movies == 0:
            dialog.create_ok(helper.language(32050)) # "Your library is up to date. Nothing to sync"
        else:
            dialog.create_ok(helper.language(32054).format(self.total_sync_movies)) # "{0} number of movies has been synchronized"


    def sync_upstream(self):
        num = self.xbmc.number_watched_movies()
        if num <= 0:
            return

        for movies in self.xbmc.watched_movies():
            approved_movies = []
            for i, movie in enumerate(movies):
                self.check_if_canceled()
                self.progress_update(i/num, helper.language(32044), movie['title']) # "Uploading movies to EpisodeHunter"
                self.total_sync_movies = self.total_sync_movies + 1
                if not self.movie_set_as_seen_on_eh(movie['imdbnumber']):
                    approved_movies.append({
                        'imdb_id': movie['imdbnumber'],
                        'title': movie['title'] or movie['originaltitle'],
                        'year': movie['year'],
                        'plays': 1,
                        'time': movie['lastplayed']
                    })
            self.connection.set_movies_watched(approved_movies)


    def sync_downstream(self):
        num = self.xbmc.number_unwatched_movies()
        if num <= 0:
            return

        for movies in self.xbmc.unwatched_movies():
            approved_movies = []
            for i, movie in enumerate(movies):
                self.check_if_canceled()
                self.progress_update(i/num, helper.language(32048), movie['title']) # "Setting movies as seen in xbmc"
                self.total_sync_movies = self.total_sync_movies + 1
                if self.movie_set_as_seen_on_eh(movie['imdbnumber']):
                    approved_movies.append(movie['movieid'])
            self.xbmc.set_movies_as_watched(approved_movies)


    def movie_set_as_seen_on_eh(self, imdb):
        for movie in self.eh_watched_movies:
            if imdb == movie['imdb_id']:
                return True
        return False

    def get_movies_from_eh(self):
        self.eh_watched_movies = self.connection.get_watched_movies()
