"""
Sync watched Movies/TV shows to Episodehunter
"""

import time
import xbmc
import xbmcaddon
import xbmcgui
#from resources.lib.connection import Connection
from resources.lib import xbmc_helper
from resources.lib import helper
from resources.lib import progress
from resources.model import movie_model

__settings__ = xbmcaddon.Addon("script.episodehunter")
__language__ = __settings__.getLocalizedString
__title__ = "EpisodeHunter"


def movie_creterial(movie):
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
        helper.debug('{0}: {1}'.format(error.errno, error.strerror))

    try:
        if 'playcount' not in movie or int(movie['playcount']) <= 0:
            return False
    except ValueError, error:
        helper.debug('{0}: {1}'.format(error.errno, error.strerror))

    return True

class Sync(object):
    """ Abstract baseclass for sync """

    def __init__(self):
        super(Sync, self).__init__()
        self.progress = None

    def create_progress(self, msg):
        self.progress = progress.create(msg)

    def quit(self):
        self.progress.close()


class SyncMovies(Sync):
    """
    Sync class
    Two-way sync between xbmc and EH
    """

    def __init__(self, connection):
        super(SyncMovies, self).__init__()
        self.connection = connection
        self.progress = None
        self.upstream_sync = []
        self.downstream_sync = []
        self.eh_watched_movies = None
        self.xbmc_watched_movies = None

    def sync(self):
        self.create_progress(__language__(32021))  # "Checking XBMC Database for new watched movies"
        self._get_movies_to_sync_upstream()
        self._get_movies_to_sync_downstream()
        self._sync()
        self.quit()

    def _sync(self):
        if len(self.upstream_sync) > 0:
            self.connection.set_movies_watched(self.upstream_sync)

    def _get_movies_to_sync_upstream(self):
        self._get_watched_movies()
        num_movies = len(self.xbmc_watched_movies)
        self.upstream_sync = []
        for i, m in enumerate(self.xbmc_watched_movies):
            self.progress.update(100 / num_movies * i)
            if not movie_creterial(m):
                continue
            if self._movie_already_synced(m['imdbnumber']):
                continue
            self.upstream_sync.append(movie_model.create_from_xbmc(m))
        # self.upstream_sync = filter(movie_creterial, self.xbmc_watched_movies)
        # self.upstream_sync = [m for m in self.upstream_sync if not self._movie_already_synced(m['imdbnumber'])]
        # self.upstream_sync = map(movie_model.create_from_xbmc, self.upstream_sync)

    def _get_movies_to_sync_downstream(self):
        pass

    def _movie_already_synced(self, imdb):
        for movie in self.eh_watched_movies:
            if imdb == movie['imdb_id']:
                return True
        return False

    def _get_watched_movies(self):
        self.eh_watched_movies = self.connection.get_watched_movies()
        self.xbmc_watched_movies = xbmc_helper.get_movies_from_xbmc()
        if self.eh_watched_movies is None:
            self.eh_watched_movies = []
        if self.xbmc_watched_movies is None:
            self.xbmc_watched_movies = []




    def movies(self, gui=True):

        if xbmc_movies is None or eh_movies is None:
            if gui:
                self.progress.close()
            return

        i = -1                          # Iterator index
        num_movies = len(xbmc_movies)   # Number of movies in XBMC database
        set_as_seen = []                # List of movie to set as seen

        for movie in xbmc_movies:
            # Increase at beginning because of 'continue' and other fancy jumps
            i += 1
            if xbmc.abortRequested:
                raise SystemExit()
            if gui:
                self.progress.update(100 / num_movies * i)
                if self.progress.iscanceled():
                    # "Progress Aborted"
                    xbmcgui.Dialog().ok(__title__, __language__(32022))
                    break
            try:
                imdb_id = movie['imdbnumber']
            except KeyError:
                helper.debug("Skipping a movie - no IMDb ID was found")
                continue

            # Is the movie listed at EpisodeHunter as watched?
            if helper.not_seen_movie(imdb_id, eh_movies):
                try:
                    playcount = movie['playcount']
                    year = movie['year']
                except KeyError:
                    continue

                if playcount > 0:                                   # Have the user watch it?
                    if year > 0:                                    # I guess that this movie is younger then Jesus?
                        if 'lastplayed' in movie:                   # Do we have a date?
                            if 'originaltitle' in movie:            # It would be great if we have the original title
                                set_as_seen.append({
                                    'imdb_id': imdb_id,
                                    'title': movie['originaltitle'],
                                    'year': movie['year'],
                                    'plays': movie['playcount'],
                                    'last_played': int(time.mktime(time.strptime(movie['lastplayed'], '%Y-%m-%d %H:%M:%S')))
                                })
                            else:                                   # No original title? Okey, send the 'ordinary' title
                                set_as_seen.append({
                                    'imdb_id': imdb_id,
                                    'title': movie['title'],
                                    'year': movie['year'],
                                    'plays': movie['playcount'],
                                    'last_played': int(time.mktime(time.strptime(movie['lastplayed'], '%Y-%m-%d %H:%M:%S')))
                                })
                        else:                                       # No 'last-play'? :(
                            if 'originaltitle' in movie:            # It would be great if we have the original title
                                set_as_seen.append({
                                    'imdb_id': imdb_id,
                                    'title': movie['originaltitle'],
                                    'year': movie['year'],
                                    'plays': movie['playcount']
                                })
                            else:                                   # Do we have any data?
                                try:
                                    set_as_seen.append({
                                        'imdb_id': imdb_id,
                                        'title': movie['title'],
                                        'year': movie['year'],
                                        'plays': movie['playcount']
                                    })
                                except KeyError:
                                    pass
                    else:
                        helper.debug("Skipping " + movie['title'] + " - The movie is to old")

        set_as_seen_title = ""
        for i in range(0, len(set_as_seen)):
            if i == 0:
                set_as_seen_title += set_as_seen[i]['title']
            elif i > 5:
                set_as_seen_title += ", ..."
                break
            else:
                set_as_seen_title += ", " + set_as_seen[i]['title']

        # Set movies as seen on EpisodeHunter:
        num_seen_movies = len(set_as_seen)
        if num_seen_movies > 0:
            if gui:
                # 'Movies will be added as watched on EpisodeHunter'
                choice = xbmcgui.Dialog().yesno(__title__, str(num_seen_movies) + " " + __language__(32023), set_as_seen_title)
            else:
                choice = True

            if choice == 1 or choice is True:  # I believe this is OS depending
                if gui:
                    self.progress.update(50, __language__(32044))  # 'Uploading movies to episodehunter'
                data = self.connection.set_movies_watched(set_as_seen)

                if data is None:
                    helper.debug("Error uploading seen movies: response is None")
                    if gui:
                        xbmcgui.Dialog().ok(__title__, __language__(32024), "")  # 'Error uploading watched movies'
                elif 'status' in data:
                    if data['status'] == 200:
                        helper.debug("successfully uploaded seen movies")
                        if gui:
                            xbmcgui.Dialog().ok(__title__, __language__(32040))  # 'Movie successfully updated to EpisodeHunter'
                    elif data['status'] == 300:
                        helper.debug("Error uploading seen movies: " + str(data['data']))
                        if gui:
                            xbmcgui.Dialog().ok(__title__, __language__(32024), str(data['data']))  # 'Error uploading watched movies'
        else:
            if gui:
                xbmcgui.Dialog().ok(__title__, __language__(32025))  # 'No new watched movies to update for EpisodeHunter'

        if gui:
            self.progress.close()



def sync_watched_series(gui=True):
    MAX_SEASON_NUMBER = 50

    if gui:                                             # Are we syncing in a GUI?
        progress = xbmcgui.DialogProgress()             # Create a dialog
        progress.create(__title__, __language__(32030))  # And put a title on it (Checking XBMC Database for new watched Episodes)

    # Create a connection
    connection = Connection()

    # Get a list of set watched episodes
    eh_tvshows = connection.get_watched_shows()
    xbmc_tvshows = xbmc_helper.get_tv_shows_from_xbmc()

    if xbmc_tvshows is None or eh_tvshows is None:
        helper.debug('xbmc_tvshows or eh_tvshows is None')
        if gui:
            progress.close()
        return

    if len(eh_tvshows) <= 0:
        # We will get a lot of errors. BUT we will catch them all
        eh_tvshows = {}

    if 'tvshows' in xbmc_tvshows:
        xbmc_tvshows = xbmc_tvshows['tvshows']

    set_as_seen = []    # List of shows to set as seen
    tvshow = {}         # The current TV show to add
    i = -1              # Iterator index
    count = 0           # Number of episode to set as watched

    number_tvshows = len(xbmc_tvshows)

    for xbmc_tvshow in xbmc_tvshows:
        i += 1                                                  # Increase at beginning because of 'continue' and other fancy
        if xbmc.abortRequested:
            raise SystemExit()
        if gui:
            progress.update(100 / number_tvshows * i)
            if progress.iscanceled():
                # "Progress Aborted"
                xbmcgui.Dialog().ok(__title__, __language__(32022))
                break

        if 'tvshowid' in xbmc_tvshow:
            # Get a list of seasons
            seasons = xbmc_helper.get_seasons_from_xbmc(xbmc_tvshow)
        else:
            helper.debug("Skipping tv show - no tvdb ID was found")
            continue

        try:
            tvshow['title'] = xbmc_tvshow['title']
            tvshow['year'] = xbmc_tvshow['year']
            tvshow['tvdb_id'] = xbmc_tvshow['imdbnumber']
            seasons = seasons['seasons']
        except KeyError:
            helper.debug("Skipping TV show - key error")
            continue

        tvshow['episodes'] = []

        number_seasons = len(seasons)

        seasonid = -1
        for _ in range(0, number_seasons):
            seasonid += 1
            while True:
                episodes = xbmc_helper.get_episodes_from_xbmc(xbmc_tvshow, seasonid)
                if 'limits' in episodes and 'total' in episodes['limits'] and episodes['limits']['total'] > 0:
                    break
                if seasonid > MAX_SEASON_NUMBER:
                    break
                if xbmc.abortRequested:
                    raise SystemExit()
                seasonid += 1
            if seasonid > MAX_SEASON_NUMBER:
                continue

            # Okay, lets stop for a moment
            # What do we have?
            # We have show title, show year, tvdb_id, season id(s) and a list of episodes

            try:
                foundseason = False
                for season in eh_tvshows[str(xbmc_tvshow['imdbnumber'])]['seasons']:
                    foundseason = True
                    # Okay, we have seen some season (no KeyError). But have we seen them all?
                    if season['season'] == str(seasonid):
                        # Okay, we have seen some episode in the season, but have we seen them all?
                        for episode in episodes['episodes']:
                            if helper.seen_episode(episode['episode'], season['episodes']):
                                # We have seen the episode, lets continue
                                continue
                            else:
                                # Add the episode
                                try:
                                    if episode['playcount'] > 0:
                                        tvshow['episodes'].append({
                                            'season': seasonid,
                                            'episode': episode['episode']})
                                        count += 1
                                except KeyError:
                                    pass
                if not foundseason:
                    raise KeyError

            except KeyError:
                # Add season as seen (whole tv show may be missing)
                for episode in episodes['episodes']:
                    try:
                        if episode['playcount'] > 0:
                            tvshow['episodes'].append({
                                'season': seasonid,
                                'episode': episode['episode']})
                            count += 1
                    except KeyError:
                        pass
                # The season have now been added, lets continue
                continue

        # If there are episodes to add to EpisodeHunter - append to list
        if len(tvshow['episodes']) > 0:
            set_as_seen.append(tvshow)
        tvshow = {}

    set_as_seen_title = ""
    for i in range(0, len(set_as_seen)):
        if i == 0:
            set_as_seen_title += set_as_seen[i]['title']
        elif i > 5:
            set_as_seen_title += ", ..."
            break
        else:
            set_as_seen_title += ", " + set_as_seen[i]['title']

    if count > 0:
        if gui:
            choice = xbmcgui.Dialog().yesno(__title__, str(count) + " " + __language__(32031), set_as_seen_title)  # String: Episodes will be added as watched
        else:
            choice = 0

        if choice == 1 or choice is True:   # I believe this is OS depending
            error = None

            number_of_watched_shows = len(set_as_seen)
            i = -1

            progress.update(0, __language__(32043))  # Uploading shows to episodehunter

            for show in set_as_seen:
                i += 1
                if xbmc.abortRequested:
                    raise SystemExit()

                if gui:
                    progress.update(100 / number_of_watched_shows * i)

                data = connection.set_shows_watched(show['tvdb_id'], show['title'], show['year'], show['episodes'])

                if data is None:
                    helper.debug("Error uploading tvshow: response is None")
                    error = ""
                elif data['status'] == 300:
                    helper.debug("Error uploading tvshow: " + show['title'] + ": " + str(data['data']))
                    error = data['data']

            if error is None:
                if gui:
                    xbmcgui.Dialog().ok(__title__, __language__(32032))            # Episodes successfully updated to EpisodeHunter
                else:
                    helper.notification(__title__, __language__(32032))                   # Episodes successfully updated to EpisodeHunter
            else:
                if gui:
                    xbmcgui.Dialog().ok(__title__, __language__(32033), error)     # Error uploading watched TVShows
                else:
                    helper.notification(__title__, __language__(32033) + str(error))      # Error uploading watched TVShows
    else:
        if gui:
            xbmcgui.Dialog().ok(__title__, __language__(32034))                    # No new watched episodes in XBMC library to update

    if gui:
        progress.close()
