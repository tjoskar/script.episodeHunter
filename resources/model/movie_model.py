import time


def create_from_xbmc(xbmc_movie):
    """
    Creating a movie model bast on xbmc model
    :rtype : Movie
    :param xbmc_movie: dic
    :return: Movie model
    """
    model = Movie()
    model.imdb_id = xbmc_movie['imdbnumber']
    model.title = xbmc_movie['originaltitle'] if 'originaltitle' in xbmc_movie else xbmc_movie['title']
    model.year = xbmc_movie['year']
    model.plays = xbmc_movie['playcount']
    model.last_played = int(time.mktime(time.strptime(xbmc_movie['lastplayed'], '%Y-%m-%d %H:%M:%S'))) if 'lastplayed' in xbmc_movie else int(time.time())
    return model


class Movie(object):
    """ Movie model """

    imdb_id = None
    title = None
    year = None
    plays = None
    last_played = None
