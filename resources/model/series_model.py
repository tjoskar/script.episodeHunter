def create_from_xbmc(xbmc_series, episodes):
    """
    Creating a movie model bast on xbmc model
    :rtype : Series
    :param xbmc_series: dic
    :return: Series model
    """

    model = Series()
    model.title = xbmc_series['title']
    model.year = xbmc_series['year']
    model.tvdb_id = xbmc_series['imdbnumber']
    model.plays = xbmc_series['playcount']
    model.episodes = [Episode(e['season'], e['episode'], e['playcount']) for e in episodes]
    return model


class Series(object):
    """ Series model """

    title = None
    year = None
    tvdb_id = None
    plays = None
    episodes = []


class Episode(object):
    """ Episode model """

    season = None
    episode = None
    plays = None

    def __init__(self, season, episode, plays):
        super(Episode, self).__init__()
        self.season = season
        self.episode = episode
        self.plays = plays
