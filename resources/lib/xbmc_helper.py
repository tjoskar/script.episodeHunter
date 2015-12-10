import json
import xbmc
import helper


def xbmc_rpc(arg):
    rpc_cmd = json.dumps(arg)
    result = xbmc.executeJSONRPC(rpc_cmd)
    result = json.loads(result)

    if 'error' in result:
        helper.debug('execute_rpc: ' + str(result['error']))
        return {'result': {}}

    return result


def execute_rpc(**kargs):
    """
    :rtype : dict
    """
    kargs['jsonrpc'] = '2.0'
    return xbmc_rpc(kargs)['result']


def get_active_players_from_xbmc():
    result = execute_rpc(method='Player.GetActivePlayers', id=1)

    try:
        return result[0]['playerid']
    except KeyError:
        helper.debug("Failing to fetch player id")
        helper.debug(result)
        return None


def get_currently_playing_from_xbmc(playerid):
    result = execute_rpc(method='Player.GetItem', params={'playerid': playerid, 'properties': ['title']}, id=1)

    try:
        return result['item']
    except KeyError:
        helper.debug("Failing to fetch playing item for player id: " + str(playerid))
        helper.debug(result)
        return None


def get_movies_from_xbmc():
    result = execute_rpc(
        method='VideoLibrary.GetMovies',
        params={
            'properties': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed']
        },
        id=1)

    return result['movies'] if 'movies' in result and isinstance(result['movies'], list) else []


def watched_shows():
    jumps = 5
    start = 0
    end = jumps
    while True:
        filter_by_playcount = {'field': 'playcount', 'operator': 'greaterthan', 'value': '0'}
        shows = get_shows(start, end, filter_by_playcount)
        start = end
        end = start + jumps
        if not shows:
            return
        for show in shows:
            if meet_show_criteria(show):
                yield show


def get_shows(start=0, end=0, filt=None):
    params = {
        'properties': ['title', 'year', 'imdbnumber', 'playcount', 'season', 'watchedepisodes']
    }
    if end != 0:
        params['limits'] = {'start': start, 'end': end}
    if filt:
        params['filter'] = filt

    result = execute_rpc(
        method='VideoLibrary.GetTVShows',
        params=params,
        id=1
    )

    return result['tvshows'] if 'tvshows' in result and isinstance(result['tvshows'], list) else []


def get_seasons_from_xbmc(tvshow, filt=None):
    if 'tvshowid' not in tvshow or tvshow['tvshowid'] == '':
        return

    params = {
        'tvshowid': tvshow['tvshowid'],
        'properties': ['watchedepisodes', 'season']
    }

    if filt:
        params['filter'] = filt

    result = execute_rpc(
        method='VideoLibrary.GetSeasons',
        params=params,
        id=1
    )

    seasons = result['seasons'] if 'seasons' in result and isinstance(result['seasons'], list) else []

    for season in seasons:
        try:
            yield season['season']
        except KeyError:
            pass


def get_watched_seasons(show):
    filter_by_playcount = {'field': 'playcount', 'operator': 'greaterthan', 'value': '0'}
    return get_seasons_from_xbmc(show, filter_by_playcount)


def get_episodes(tvshow, season, filt=None):
    if 'tvshowid' not in tvshow or tvshow['tvshowid'] == '':
        return []

    params = {'tvshowid': tvshow['tvshowid'], 'season': season, 'properties': ['playcount', 'episode', 'season']}
    if filt:
        params['filter'] = filt

    result = execute_rpc(
        method='VideoLibrary.GetEpisodes',
        params=params,
        id=1
    )

    return result['episodes'] if 'episodes' in result and isinstance(result['episodes'], list) else []


def get_watched_episodes(show, season):
    filter_by_playcount = {'field': 'playcount', 'operator': 'greaterthan', 'value': '0'}
    return get_episodes(show, season, filter_by_playcount)


def get_movie_details_from_xbmc_by_title(title, year, fields):
    result = execute_rpc(method='VideoLibrary.GetMovieDetails', params={'title': title, 'year': year, 'properties': fields}, id=1)
    return result['moviedetails'] if 'moviedetails' in result else None


def get_movie_details_from_xbmc(library_id):
    result = execute_rpc(
        method='VideoLibrary.GetMovieDetails',
        params={
            'movieid': library_id,
            'properties': ['year', 'imdbnumber', 'originaltitle']
        },
        id=1)

    return result['moviedetails'] if 'moviedetails' in result else None


def get_episode_details_from_xbmc(library_id):
    result = execute_rpc(
        method='VideoLibrary.GetEpisodeDetails',
        params={
            'episodeid': library_id,
            'properties': ['tvshowid', 'showtitle', 'season', 'episode']
        },
        id=1)

    return result['episodedetails'] if 'episodedetails' in result else None


def get_show_details_from_xbmc(library_id):
    result = execute_rpc(
        method='VideoLibrary.GetTVShowDetails',
        params={
            'tvshowid': library_id,
            'properties': ['imdbnumber', 'year']
        },
        id=1)

    return result['tvshowdetails'] if 'tvshowdetails' in result else None


def set_movie_as_watched(movie_id):
    execute_rpc(method='VideoLibrary.SetMovieDetails', params={'movieid': movie_id, "playcount": 1}, id=1)


def set_movies_as_watched(movies):
    movies_rpc = [{
        'jsonrpc': '2.0',
        'method': 'VideoLibrary.SetMovieDetails',
        'params': {'movieid': m.xbmc_id, 'playcount': 1},
        'id': i
    } for i, m in enumerate(movies)]

    map(xbmc_rpc, helper.chunks(movies_rpc, 50))


def set_series_as_watched(series):
    episodes = []
    for s in series:
        episodes = episodes + [{
            'jsonrpc': '2.0',
            'method': 'VideoLibrary.SetEpisodeDetails',
            'params': {'episodeid': e.xbmc_id, 'playcount': 1},
            'id': i
        } for i, e in enumerate(s.episodes)]

    map(xbmc_rpc, helper.chunks(episodes, 50))


def meet_show_criteria(tvshow):
    if 'title' not in tvshow or not tvshow['title']:
        return False

    try:
        int(tvshow['imdbnumber'])
    except (ValueError, TypeError):
        return False

    try:
        if 'year' not in tvshow or int(tvshow['year']) <= 0:
            return False
    except ValueError:
        return False

    return True
