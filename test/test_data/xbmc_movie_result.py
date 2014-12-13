import copy

MOVIES = [
    {
        'imdbnumber': 'tt1392170',
        'playcount': '3',
        'originaltitle': 'The Hunger Games',
        'title': 'The Hunger Games',
        'year': '2011',
        'lastplayed': '2014-10-10 20:03:31'
    }, {
        'imdbnumber': 'tt1440129',
        'playcount': '1',
        'originaltitle': 'Battleship',
        'title': 'Battleship',
        'year': '2011',
        'lastplayed': '1989-09-27 11:20:31'
    }, {
        'imdbnumber': 'tt0905372',
        'playcount': '1',
        'originaltitle': 'The Thing',
        'title': 'The Thing',
        'year': '2011',
        'lastplayed': '2014-12-01 22:03:31'
    }
]


def get(*args, **kargs):
    """
    Returning a list of movies according to xbmc's model
    :rtype : list
    :param args:str names of movies
    :param kargs:list   remove_attr, list of attr to remove
    :return: list
    """
    return_list = [copy.copy(x) for x in MOVIES if x['title'] in args]

    if 'remove_attr' in kargs:
        return_list = [{i: m[i] for i in m if i not in kargs['remove_attr']} for m in return_list]
    return return_list
