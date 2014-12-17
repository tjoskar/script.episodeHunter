"""
Background process
"""

import time
import json
import xbmc
import xbmcaddon
from resources.lib import helper
from resources.lib import xbmc_helper
from resources.lib import user
from resources.lib.database import Database
from resources.lib.connection import Connection
from resources.lib.connection import Http
from resources import config


def is_movie(media):
    return 'type' in media and media['type'] == 'movie'


def is_episode(media):
    return 'type' in media and media['type'] == 'episode'


def is_media(media):
    return media is not None and 'type' in media and 'id' in media


class EHPlayer(xbmc.Player):

    is_playing = False           # Is XBMC playing a video right now?
    __current_video = None       # The current video object
    __total_time = 0             # Total time of the movie/TV-show
    __watched_time = 0           # Total watched time
    __is_active = False          # True if pause || playing
    __valid_user = True          # Is the settings OK?
    __offline = False            # Are we offline?
    __media = None               # Current media
    __db = None                  # Database object
    __connection = None          # Connection object

    def __init__(self):
        xbmc.Player.__init__(self)
        db_path = helper.get_addon_resource_path('/offline.db')
        self.__db = Database(db_path)
        self.__connection = Connection(Http(config.__BASE_URL__))

    def reset_var(self):
        """ Reset all values to there defaults """
        self.is_playing = False
        self.__current_video = None
        self.__total_time = 0
        self.__watched_time = 0
        self.__is_active = False
        self.__valid_user = True
        self.__offline = False
        self.__media = None

    def onPlayBackStarted(self):
        """
        Will be called when xbmc starts playing a file.
        """
        helper.debug("onPlayBackStarted")
        self.reset_var()
        self.check_user(silent=False)  # Check if we have the user-data we need

        # Do we actually play a video
        if xbmc.Player().isPlayingVideo():
            player_id = xbmc_helper.get_active_players_from_xbmc()
            self.__current_video = xbmc_helper.get_currently_playing_from_xbmc(player_id)
            if is_media(self.__current_video):
                if not xbmc.Player().isPlayingVideo():
                    return None

                if is_movie(self.__current_video):
                    self.__media = xbmc_helper.get_movie_details_from_xbmc(self.__current_video['id'])

                elif is_episode(self.__current_video):
                    self.__media = xbmc_helper.get_episode_details_from_xbmc(self.__current_video['id'])
                    if self.__media is None:
                        # Did not find current episode
                        return
                    series_match = xbmc_helper.get_show_details_from_xbmc(self.__media['tvshowid'])
                    self.__media['imdbnumber'] = series_match['imdbnumber']
                    self.__media['year'] = series_match['year']

                self.__total_time = xbmc.Player().getTotalTime()
                self.is_playing = True
                self.__is_active = True
            else:
                self.reset_var()

    def onPlayBackEnded(self):
        """ Called when the playback is ending """
        helper.debug("onPlayBackEnded")
        self.__watched_time = self.__total_time
        self.onPlayBackStopped()

    def onPlayBackStopped(self):
        """ Called when the user stops the playback """
        helper.debug("onPlayBackStopped")
        if self.__is_active:
            helper.debug("onPlayBackStopped Stopped after: " + str(self.__watched_time))
            if is_media(self.__current_video):  # If the current_video is None, something is wrong
                self.reset_var()
                return None
            self.scrobble()

            self.reset_var()

    def onPlayBackPaused(self):
        """ On pause """
        helper.debug("onPlayBackPaused")
        if self.__is_active and self.is_playing:  # Are we really playing?
            self.is_playing = False               # Okay then, lets pause
            self.update_watched_time()            # Update the playing time

    def onPlayBackResumed(self):
        """ On resumed """
        helper.debug("onPlayBackResumed")
        # Have the user update his user setting while pausing?
        self.check_user(silent=True)
        if self.__is_active:
            self.is_playing = True

    def update_watched_time(self):
        """ Update the time a user has watch an episode/move """
        self.__watched_time = helper.xbmc_time_to_seconds(str(xbmc.getInfoLabel("Player.Time")))

    def watching(self):
        """ This functions is called continuously, see below """
        helper.debug("watching, is_playing: " + str(self.is_playing))
        if self.is_playing and self.__media is not None:

            self.update_watched_time()

            if not self.__valid_user or self.__offline:
                return None

            if is_movie(self.__current_video) and user.scrobble_movies():
                self.communicate_with_eh(
                    self.__connection.watching_movie,
                    self.__media['originaltitle'],
                    self.__media['year'],
                    self.__media['imdbnumber'],
                    self.__total_time / 60,
                    int(100 * self.__watched_time / self.__total_time)
                )
            elif is_episode(self.__current_video) and user.scrobble_episodes():
                self.communicate_with_eh(
                    self.__connection.watching_episode,
                    self.__media['imdbnumber'],
                    self.__media['showtitle'],
                    self.__media['year'],
                    self.__media['season'],
                    self.__media['episode'],
                    self.__total_time / 60,
                    int(100 * self.__watched_time / self.__total_time)
                )

    def stop_watching(self):
        """ Tell episodehunter.tv that we have stop watching """
        helper.debug("stoppedWatching")

        if self.__valid_user and not self.__offline:
            if is_movie(self.__current_video) and user.scrobble_movies():
                self.communicate_with_eh(self.__connection.cancel_watching_movie)
            elif is_episode(self.__current_video) and self.__scrobble_episode:
                self.communicate_with_eh(self.__connection.cancel_watching_episode)

    def scrobble(self):
        """ Scrobble a movie / episode """
        helper.debug("scrobble")

        scrobble_min_view_time_option = self.__settings.getSetting("scrobble_min_view_time")

        if (self.__watched_time / self.__total_time) * 100 >= float(scrobble_min_view_time_option):
            responce = None
            if self.__current_video['type'] == 'movie' and self.__scrobble_movie:
                try:
                    arg = {}
                    arg['method'] = 'scrobble_movie'
                    arg['parameter'] = {'originaltitle': self.__media['originaltitle'],
                                        'year': self.__media['year'],
                                        'imdb_id': self.__media['imdbnumber'],
                                        'duration': self.__total_time / 60,
                                        'percent': int(100 * self.__watched_time / self.__total_time),
                                        'timestamp': int(time.time())}

                    if self.__offline or not self.__valid_user:
                        self.__db.write(arg)
                        return None

                    responce = self.__connection.scrobble_movie(**arg['parameter'])

                except Exception:
                    helper.debug("scrobble: Something went wrong (movie)")

            elif self.__current_video['type'] == 'episode' and self.__scrobble_episode:
                try:
                    arg = {}
                    arg['method'] = 'scrobble_episode'
                    arg['parameter'] = {'tvdb_id': self.__media['imdbnumber'],
                                        'title': self.__media['showtitle'],
                                        'year': self.__media['year'],
                                        'season': self.__media['season'],
                                        'episode': self.__media['episode'],
                                        'duration': self.__total_time / 60,
                                        'percent': int(100 * self.__watched_time / self.__total_time),
                                        'timestamp': int(time.time())}

                    if self.__offline or not self.__valid_user:
                        self.__db.write(arg)
                        return None

                    responce = self.__connection.scrobble_episode(**arg['parameter'])

                except Exception, e:
                    print e
                    helper.debug("scrobble: Something went wrong (episode)")

            if responce is None or ('status' in responce and responce['status'] != 200):
                self.__db.write(arg)
                return None
            else:
                helper.debug("Scrobble responce: " + str(responce))

        else:
            self.stop_watching()

    def communicate_with_eh(self, method, *args):
        try:
            method(*args)
        except Exception:
            pass

    def check_for_old_data(self):
        """ Check the database for old offline data """
        helper.debug("check_for_old_data")

        success = []

        if not self.__offline:
            rows = self.__db.get_all()

            if rows is None or not rows:
                helper.debug("check_for_old_data: No rows")
                return None

            try:
                for row in rows:
                    try:
                        data = json.loads(row[1])
                    except Exception:
                        helper.debug("check_for_old_data: unable to convert string to json: " + str(row[1]))
                        continue

                    try:
                        helper.debug('Make the call')
                        responce = getattr(self.__connection, data['method'])(**data['parameter'])
                        if responce is None or ('status' in responce and responce['status'] != 200):
                            helper.debug("check_for_old_data: Unable to get responce. m: " + str(data['method']) + " p: " + str(data['parameter']))
                            break
                        else:
                            success.append(row[0])
                    except Exception:
                        helper.debug("Unable to call function: " + str(data))
                        success.append(row[0])

            except Exception:
                helper.debug("check_for_old_data: Unable to loop")

            if len(success) > 0:
                helper.debug("Remove id: " + str(success))
                self.__db.remove_rows(success)

    def check_user(self, silent):
        """ Check if the user-settings are correct """
        # Check if we have the user-data we need.
        if not helper.is_settings_okey(daemon=True, silent=silent):
            self.__valid_user = False
        else:
            self.__valid_user = True


player = EHPlayer()

player.check_for_old_data()
i = 0
while not xbmc.abortRequested:
    xbmc.sleep(1000)
    if player.is_playing:
        i += 1
        if i >= 300:
            player.watching()
            i = 0
