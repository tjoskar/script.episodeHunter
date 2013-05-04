import xbmc
import xbmcaddon
import time
import socket

# http://stackoverflow.com/questions/712791/json-and-simplejson-module-differences-in-python
try:
    import simplejson as json
except ImportError:
    import json

from httpconn import *
from helper import *


class Connection(object):

    def __init__(self):
        self.settings = xbmcaddon.Addon("script.episodeHunter")
        self.language = self.settings.getLocalizedString
        self.name = "EpisodeHunter"
        self.URL = "api.episodehunter.tv"
        self.connection = None

    def makeConnection(self):
        try:
            self.connection = HTTPConn(self.URL, 80)
        except socket.timeout:
            Debug("makeConnection: timeout")
            notification(self.name, self.language(10055))
            self.connection = None

    # Contact EpisodeHunter
    def makeRequest(self, request, args={}):

        # Must have username as wall as apikey
        if self.settings.getSetting("username") == "" or self.settings.getSetting("api_key") == "":
            return None

        # Create an connection
        self.makeConnection()
        if self.connection is None:
            Debug("Unable to connect")
            return None

        try:
            args['username'] = self.settings.getSetting("username")
            args['apikey'] = self.settings.getSetting("api_key")

            jdata = json.dumps(args)
        except Exception:
            Debug("makeRequest: Unable to create json object: " + str(args))
            return None

        # Create the request
        try:
            self.connection.request(request, jdata)
            Debug("The data has left XBMC: " + request)
        except socket.error:
            Debug("makeRequest: Socket error, unable to connect")
            notification(self.name, self.language(10056))
            return None

        # And off we go
        try:
            self.connection.go()
        except Exception:
            Debug("makeRequest: Unable to send data")
            notification(self.name, self.language(10061))
            return None

        # Wait for the respond, timeout after 15s
        i = 0
        while True:
            if self.connection.hasResult() or xbmc.abortRequested:
                if xbmc.abortRequested:
                    Debug("makeRequest: Dude? Can't get respond if you break the loop")
                    return None
                break

            time.sleep(1)
            i = i + 1
            if i >= 15:
                Debug("makeRequest: Connection timeout")
                notification(self.name, self.language(10055))
                return None

        # Ladies and gentlemen, we have a result
        try:
            response = self.connection.getResult()
            raw = response.read()
        except Exception:
            Debug("Unable to read responce")
            notification(self.name, self.language(10062))
            return None
        finally:
            try:
                # The average time for every request is five minutes
                # so we might as well close the connection. (Apache has the connection open for about 3 minutes)
                self.connection.close()
            except Exception:
                pass

        try:
            data = json.loads(raw)
        except ValueError:
            Debug("makeRequest: Bad JSON responce: " + raw)
            notification(self.name, self.language(10057))
            return None

        if 'status' in data and 'data' in data:
            if data['status'] == 300:
                Debug("makeRequest: Error: " + str(data['data']))
                notification(self.name, self.language(10035) + ": " + str(data['data']))
                return None

        return data

    def setMoviesSeen(self, movies_seen=[]):
        return self.makeRequest('/movie/watched', {'movies': movies_seen})

    def setTvSeen(self, tvdb_id, title, year, episodes):
        return self.makeRequest('/tv/watched', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'episodes': episodes})

    def getMoviesFromEP(self):
        responce = self.makeRequest('/movie/getWatched')
        if responce is None:
            Debug("getMoviesFromEP: Error")
        elif 'value' in responce:
            return responce['value']
        return None

    def getWatchedTVShowsFromEH(self):
        responce = self.makeRequest('/tv/getWatched')
        if responce is None:
            Debug("getWatchedTVShowsFromEH: Error")
        elif 'value' in responce:
            return responce['value']
        return None

    def watchingMovie(self, imdb_id, duration, percent):
        responce = self.makeRequest('/movie/watching', {'imdb_id': imdb_id, 'duration': duration, 'progress': percent})
        if responce is None:
            Debug("watchingMovie: Error")
        return responce

    def watchingEpisode(self, tvdb_id, title, year, season, episode, duration, percent):
        responce = self.makeRequest('/tv/watching', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progress': percent})
        if responce is None:
            Debug("watchingEpisode: Error")
        return responce

    def cancelWatchingMovie(self):
        responce = self.makeRequest('/movie/cancelWatching', {})
        if responce is None:
            Debug("cancelWatchingMovie: Error")
        return responce

    def cancelWatchingEpisode(self):
        responce = self.makeRequest('/tv/cancelWatching', {})
        if responce is None:
            Debug("cancelWatchingEpisode: Error")
        return responce

    def scrobbleMovie(self, imdb_id, duration, percent):
        responce = self.makeRequest('/movie/scrobble', {'imdb_id': imdb_id, 'duration': duration, 'progress': percent})
        if responce is None:
            Debug("scrobbleMovie: Error")
        return responce

    def scrobbleEpisode(self, tvdb_id, title, year, season, episode, duration, percent):
        responce = self.makeRequest('/tv/scrobble', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progress': percent})
        if responce is None:
            Debug("scrobbleEpisode: Error")
        return responce

    def tesconn(self):
        responce = self.makeRequest('/userc/testuser')
        if responce is None:
            Debug("testconn: Error")
        return responce
