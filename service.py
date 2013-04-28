from helper import *
from xbmc_helper import *
from connection_helper import Connection
from database import Database
import traceback


class EHPlayer(xbmc.Player):

    def __init__(self):
        xbmc.Player.__init__(self)
        self.resetVar()
        path = self.settings.getAddonInfo('path')
        self.db = Database(path + "/sqlite.db")
        self.connection = Connection()

    def resetVar(self):
        self.current_video = None
        self.total_time = 0
        self.watched_time = 0
        self.is_playing = False
        self.is_active = False
        self.valid_user = True
        self.movie_IMDB = ''
        self.offline = False
        self.scrobbleMovie = True
        self.scrobbleEpisode = True

        # Reload settings
        self.settings = xbmcaddon.Addon("script.episodeHunter")
        self.language = self.settings.getLocalizedString
        self.name = "EpisodeHunter"

        offlineOption = self.settings.getSetting("offline")
        scrobbleMovieOption = self.settings.getSetting("scrobble_movie")
        scrobbleEpisodeOption = self.settings.getSetting("scrobble_episode")

        if offlineOption == 'true':
            self.offline = True
        if scrobbleMovieOption == 'false':
            self.scrobbleMovie = False
        if scrobbleEpisodeOption == 'false':
            self.scrobbleEpisode = False

    def onPlayBackStarted(self):
        Debug("onPlayBackStarted")
        self.resetVar()
        if not isSettingsOkey(True):
            self.offline = True

        if xbmc.Player().isPlayingVideo():
            playerID = getActivePlayersFromXBMC()
            self.current_video = getCurrentlyplayFromXBMC(playerID)
            if self.current_video is not None:
                if 'type' in self.current_video and 'id' in self.current_video:

                    if not xbmc.Player().isPlayingVideo():
                        Debug("What? Not playing anymore")
                        return None

                    if self.current_video['type'] == 'movie':
                        self.movie_IMDB = xbmc.Player().getVideoInfoTag().getIMDBNumber()

                    self.total_time = xbmc.Player().getTotalTime()
                    self.is_playing = True
                    self.is_active = True
                    Debug("self.total_time: " + str(self.total_time))
                    #self.watching()
            else:
                self.resetVar()

    def onPlayBackEnded(self):
        Debug("onPlayBackEnded")
        self.onPlayBackStopped()

    def onPlayBackStopped(self):
        Debug("onPlayBackStopped")
        if self.is_active:
            Debug("onPlayBackStopped Stopped after: " + str(self.watched_time))
            if self.current_video is None:
                self.resetVar()
                return None

            if 'type' in self.current_video and 'id' in self.current_video:
                self.scrobble()

            self.resetVar()

    def onPlayBackPaused(self):
        Debug("onPlayBackPaused")
        if self.is_active and self.is_playing:
            self.is_playing = False
            self.updateWatched_time()
            if self.watched_time > 0:
                Debug("onPlayBackPaused Paused after: " + str(self.watched_time))

    def onPlayBackResumed(self):
        Debug("onPlayBackResumed")
        if self.is_active:
            Debug("onPlayBackResumed self.watched_time: " + str(self.watched_time))
            self.is_playing = True

    def updateWatched_time(self):
        self.watched_time = to_seconds(str(xbmc.getInfoLabel("Player.Time")))

    def watching(self):
        Debug("watching, is_playing: " + str(self.is_playing))
        if self.is_playing:

            self.updateWatched_time()

            if self.current_video['type'] == 'movie' and self.scrobbleMovie and self.valid_user and not self.offline:
                responce = self.connection.watchingMovie(self.movie_IMDB, self.total_time / 60, int(100 * self.watched_time / self.total_time))
                if responce is not None:
                    Debug("watching: Watch responce: " + str(responce))

            elif self.current_video['type'] == 'episode' and self.scrobbleEpisode and self.valid_user and not self.offline:
                match = getEpisodeDetailsFromXbmc(self.current_video['id'], ['tvshowid', 'showtitle', 'season', 'episode'])
                if match is None:
                    Debug("watching: Did not find id")
                    return
                imdb_match = getShowDetailsFromXbmc(match['tvshowid'], ['imdbnumber'])
                if imdb_match is None:
                    Debug("watching: Did not find imdbnumber")
                    return
                responce = self.connection.watchingEpisode(imdb_match['imdbnumber'], match['showtitle'], None, match['season'], match['episode'], self.total_time / 60, int(100 * self.watched_time / self.total_time))
                if responce is not None:
                    Debug("watching Watch responce: " + str(responce))

    def stoppedWatching(self):
        Debug("stoppedWatching")

        if self.current_video['type'] == 'movie' and self.scrobbleMovie and self.valid_user and not self.offline:
            responce = self.connection.cancelWatchingMovie()
            if responce is not None:
                Debug("stoppedWatching Cancel watch responce: " + str(responce))
        elif self.current_video['type'] == 'episode' and self.scrobbleEpisode and self.valid_user and not self.offline:
            responce = self.connection.cancelWatchingEpisode()
            if responce is not None:
                Debug("stoppedWatching Cancel watch responce: " + str(responce))

    def scrobble(self):
        Debug("scrobble")

        scrobbleMinViewTimeOption = self.settings.getSetting("scrobble_min_view_time")
        Debug("Scrobble self.watched_time: " + str(self.watched_time) + " self.total_time: " + str(self.total_time))

        if self.valid_user:
            if (self.watched_time / self.total_time) * 100 >= float(scrobbleMinViewTimeOption):

                if self.current_video['type'] == 'movie' and self.scrobbleMovie:
                    arg = {}
                    arg['method'] = 'scrobbleMovie'
                    arg['parameter'] = {'imdb_id': self.movie_IMDB,
                                        'duration': self.total_time / 60,
                                        'percent': int(100 * self.watched_time / self.total_time)}

                    if self.offline:
                        self.db.write(arg)
                        return None

                    responce = self.connection.scrobbleMovie(**arg['parameter'])

                    if responce is None:
                        self.db.write(arg)
                        return None
                    else:
                        Debug("Scrobble responce: " + str(responce))

                elif self.current_video['type'] == 'episode' and self.scrobbleEpisode:

                    match = getEpisodeDetailsFromXbmc(self.current_video['id'], ['tvshowid', 'showtitle', 'season', 'episode'])
                    if match is None:
                        return None

                    imdb_match = getShowDetailsFromXbmc(match['tvshowid'], ['imdbnumber'])
                    if imdb_match is None:
                        Debug("scrobble: Hitta inte imdbnumber")
                        return None

                    arg = {}
                    arg['method'] = 'scrobbleEpisode'
                    arg['parameter'] = {'tvdb_id': imdb_match['imdbnumber'],
                                        'title': match['showtitle'],
                                        'year': None,
                                        'season': match['season'],
                                        'episode': match['episode'],
                                        'duration': self.total_time / 60,
                                        'percent': int(100 * self.watched_time / self.total_time)}

                    if self.offline:
                        self.db.write(arg)
                        return None

                    responce = self.connection.scrobbleEpisode(**arg['parameter'])

                    if responce is None:
                        self.db.write(arg)
                        return None
                    else:
                        Debug("scrobble responce: " + str(responce))
                else:
                    self.stoppedWatching()
            else:
                self.stoppedWatching()

    def checkForOldData(self):
        Debug("checkForOldData")

        success = {}

        if not self.offline:
            rows = self.db.getAll()

            if rows is None:
                Debug("checkForOldData: No rows")
                return None

            try:
                for row in rows:

                    try:
                        data = json.loads(row[1])
                    except Exception:
                        Debug("checkForOldData: unable to convert string to json: " + str(row[1]))
                        continue

                    try:
                        Debug('Make the call')
                        responce = getattr(self.connection, data['method'])(**data['parameter'])
                        if responce is None:
                            Debug("checkForOldData: Unable to get responce. m: " + str(data['method']) + " p: " + str(data['parameter']))
                            break
                        else:
                            Debug("success")
                            success[row[0]] = 1
                    except Exception:
                        Debug("Unable to call funcation: " + str(data))

            except Exception:
                Debug("checkForOldData: Unable to loop")
                print(traceback.format_exc())

            success = success.keys()
            if len(success) > 0:
                Debug("Remove id: " + str(success))
                self.db.removeRows(success)

    def isUserOK(self):
        Debug("isUserOK")
        resp = tesconn()
        if resp is None or resp['status'] == 300:
            notification(self.name, self.language(10059))
            self.valid_user = False
        else:
            self.valid_user = True


player = EHPlayer()


player.checkForOldData()
Debug("OK, lets do this")
i = 0
while(not xbmc.abortRequested):
    xbmc.sleep(1000)
    if player.is_playing and player.valid_user:
        i += 1
        if i >= 300:
            player.watching()
            i = 0

Debug("The END")
