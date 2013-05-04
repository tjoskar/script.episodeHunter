import xbmc
import xbmcaddon
import xbmcgui
from connection_helper import Connection
from xbmc_helper import *

_settings = xbmcaddon.Addon("script.episodeHunter")
_language = _settings.getLocalizedString
_name = "EpisodeHunter"


def syncSeenMovies(gui=True):

    if gui:
        progress = xbmcgui.DialogProgress()
        progress.create(_name, _language(10038))

    connection = Connection()

    EH_movies = connection.getMoviesFromEP()
    xbmc_movies = getMoviesFromXBMC()

    if xbmc_movies is None or xbmc_movies is None or EH_movies is None:
        if gui:
            progress.close()
        return

    movies_seen = []

    for i in range(0, len(xbmc_movies)):
        if xbmc.abortRequested:
            raise SystemExit()
        if gui:
            progress.update(100 / len(xbmc_movies) * i)
            if progress.iscanceled():
                xbmcgui.Dialog().ok(_name, _language(10039))
                break
        try:
            imdbid = xbmc_movies[i]['imdbnumber']
        except KeyError:
            Debug("Skipping a movie - no IMDbID was found")
            continue

        if notSeenMovie(imdbid, EH_movies):
            if xbmc_movies[i]['playcount'] > 0:
                if xbmc_movies[i]['year'] > 0:
                    try:
                        xbmc_movies[i]['lastplayed']
                        try:
                            movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['originaltitle'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount'], 'last_played': int(time.mktime(time.strptime(xbmc_movies[i]['lastplayed'], '%Y-%m-%d %H:%M:%S')))})
                        except KeyError:
                            movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['title'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount'], 'last_played': int(time.mktime(time.strptime(xbmc_movies[i]['lastplayed'], '%Y-%m-%d %H:%M:%S')))})
                    except KeyError:
                        try:
                            movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['originaltitle'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount']})
                        except KeyError:
                            movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['title'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount']})
                else:
                    Debug("Skipping " + xbmc_movies[i]['title'] + " - unknown movie")
            continue

    movies_string = ""
    for i in range(0, len(movies_seen)):
        if i == 0:
            movies_string += movies_seen[i]['title']
        elif i > 5:
            movies_string += ", ..."
            break
        else:
            movies_string += ", " + movies_seen[i]['title']

    # Set movies as seen on EpisodeHunter:
    if len(movies_seen) > 0:
        if gui:
            choice = xbmcgui.Dialog().yesno(_name, str(len(movies_seen)) + " " + _language(10040), movies_string)
            if choice is False:
                if gui:
                    progress.close()
                return

        data = connection.setMoviesSeen(movies_seen)

        if data['status'] == 400:
            Debug("successfully uploaded seen movies")
            xbmcgui.Dialog().ok(_name, _language(10058))
        elif data['status'] == 300:
            Debug("Error uploading seen movies: " + str(data['data']))
            if gui:
                xbmcgui.Dialog().ok(_name, _language(10041), str(data['data']))
    else:
        if gui:
            xbmcgui.Dialog().ok(_name, _language(10042))

    if gui:
        progress.close()


def syncSeenTVShows(gui=True):

    if gui:
        progress = xbmcgui.DialogProgress()
        progress.create(_name, _language(10047))

    connection = Connection()

    EH_tvshowlist = connection.getWatchedTVShowsFromEH()
    xbmc_tvshows = getTVShowsFromXBMC()

    if xbmc_tvshows is None or EH_tvshowlist is None:
        return

    EH_tvshows = EH_tvshowlist

    set_as_seen = []
    seasonid = -1
    tvshow = {}

    for i in range(0, xbmc_tvshows['limits']['total']):
        if xbmc.abortRequested:
            raise SystemExit()
        if gui:
            progress.update(100 / xbmc_tvshows['limits']['total'] * i)
            if progress.iscanceled():
                xbmcgui.Dialog().ok(_name, _language(10039))
                break

        seasons = getSeasonsFromXBMC(xbmc_tvshows['tvshows'][i])
        try:
            tvshow['title'] = xbmc_tvshows['tvshows'][i]['title']
            tvshow['year'] = xbmc_tvshows['tvshows'][i]['year']
            tvshow['tvdb_id'] = xbmc_tvshows['tvshows'][i]['imdbnumber']
        except KeyError:
            continue

        tvshow['episodes'] = []

        for j in range(0, seasons['limits']['total']):
            while True:
                seasonid += 1
                episodes = getEpisodesFromXBMC(xbmc_tvshows['tvshows'][i], seasonid)
                if episodes['limits']['total'] > 0:
                    break
                if seasonid > 50:
                    break
            if seasonid > 50:
                continue

            try:
                foundseason = False
                for k in range(0, len(EH_tvshows[str(xbmc_tvshows['tvshows'][i]['imdbnumber'])]['seasons'])):
                    if EH_tvshows[str(xbmc_tvshows['tvshows'][i]['imdbnumber'])]['seasons'][str(k)]['season'] == str(seasonid):
                        foundseason = True
                        for l in range(0, len(episodes['episodes'])):
                            if seenEpisode(episodes['episodes'][l]['episode'], EH_tvshows[str(xbmc_tvshows['tvshows'][i]['imdbnumber'])]['seasons'][str(k)]['episodes']):
                            #if episodes['episodes'][l]['episode'] in EH_tvshows[str(xbmc_tvshows['tvshows'][i]['imdbnumber'])]['seasons'][str(k)]['episodes']:
                                continue
                            else:
                                # Add episode as seen if playcount > 0
                                try:
                                    if episodes['episodes'][l]['playcount'] > 0:
                                        tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][l]['episode']})
                                except KeyError:
                                    continue
                if foundseason is False:
                    # Add season
                    for k in range(0, len(episodes['episodes'])):
                        try:
                            if episodes['episodes'][k]['playcount'] > 0:
                                tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][k]['episode']})
                        except KeyError:
                                    pass
            except KeyError:
                # Add season as seen (whole tv show missing)
                for k in range(0, len(episodes['episodes'])):
                    try:
                        if episodes['episodes'][k]['playcount'] > 0:
                            tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][k]['episode']})
                    except KeyError:
                        pass

        seasonid = -1
        # If there are episodes to add to EpisodeHunter - append to list
        if len(tvshow['episodes']) > 0:
            set_as_seen.append(tvshow)
            tvshow = {}
        else:
            tvshow = {}

    count = 0
    set_as_seen_titles = ""
    for i in range(0, len(set_as_seen)):
        if i == 0:
            set_as_seen_titles += set_as_seen[i]['title']
        elif i > 5:
            break
        else:
            set_as_seen_titles += ", " + set_as_seen[i]['title']
        for j in range(0, len(set_as_seen[i]['episodes'])):
            count += 1

    if count > 0:
        if gui:
            choice = xbmcgui.Dialog().yesno(_name, str(count) + " " + _language(10048), set_as_seen_titles)
        else:
            choice = True

        if choice is True:
            error = None

            for i in range(0, len(set_as_seen)):
                if xbmc.abortRequested:
                    raise SystemExit()
                data = connection.setTvSeen(set_as_seen[i]['tvdb_id'], set_as_seen[i]['title'], set_as_seen[i]['year'], set_as_seen[i]['episodes'])

                if data['status'] == 'error':
                    Debug("Error uploading tvshow: " + set_as_seen[i]['title'] + ": " + str(data['data']))
                    error = data['data']
                else:
                    Debug("Successfully uploaded tvshow " + set_as_seen[i]['title'] + ": " + str(data['data']))

            if error is None:
                if gui:
                    xbmcgui.Dialog().ok(_name, _language(10049))
                else:
                    notification(_name, _language(10049))
            else:
                if gui:
                    xbmcgui.Dialog().ok(_name, _language(10050), error)
                else:
                    notification(_name, _language(10050) + str(error))
    else:
        if gui:
            xbmcgui.Dialog().ok(_name, _language(10051))

    if gui:
        progress.close()
