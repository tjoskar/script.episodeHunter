import time

def get_key(obj, key, default=None):
    if key in obj:
        return obj[key]
    else:
        return default


def create_from_xbmc(xbmc_movie):
    """
    Creating a movie model bast on xbmc model
    :rtype : Movie
    :param xbmc_movie: dic
    :return: Movie model
    """
    model = Movie()
    model.imdb_id = get_key(xbmc_movie, 'imdbnumber')
    model.title = xbmc_movie['originaltitle'] if 'originaltitle' in xbmc_movie else xbmc_movie['title']
    model.year = get_key(xbmc_movie, 'year')
    model.plays = get_key(xbmc_movie, 'playcount', -1)
    model.last_played = int(time.mktime(time.strptime(xbmc_movie['lastplayed'], '%Y-%m-%d %H:%M:%S'))) if 'lastplayed' in xbmc_movie else int(time.time())
    return model


class Movie(object):
    """ Movie model """

    imdb_id = None
    title = None
    year = None
    plays = None
    last_played = None
