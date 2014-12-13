"""
Helper Functions
"""

import xbmc
import xbmcaddon
import xbmcgui

from resources.exceptions import SettingsExceptions

__name__ = "EpisodeHunter"
settings = xbmcaddon.Addon("script.episodehunter")
language = settings.getLocalizedString


def get_username():
    return settings.getSetting("username")


def get_api_key():
    return settings.getSetting("api_key")


def debug(msg):
    """ Prints debug message if debugging is enable in the user settings """
    is_debuging = settings.getSetting("debug")
    if is_debuging:
        try:
            xbmc.log(__name__ + ": " + msg)
        except Exception:
            try:
                xbmc.log(__name__ + ": You are trying to print some bad string, " + msg.encode("utf-8", "ignore"))
            except Exception:
                xbmc.log(__name__ + ": You are trying to print a bad string, I can not even print it")


def notification(header, message, level=0):
    """
    Create a notification and show it in 5 sec
    If debugging is enable in the user settings or the level is 0
    """
    is_debuging = settings.getSetting("debug")
    if is_debuging or level == 0:
        xbmc.executebuiltin("XBMC.Notification(%s,%s,%i,%s)" % (header, message, 5000, settings.getAddonInfo("icon")))


def check_user_credentials():
    """
    Make a local check of the user credentials
    May raise SettingsExceptions
    :rtype : bool
    """
    if get_username() == "" and get_api_key() == "":
        raise SettingsExceptions(language(32014))
    elif settings.getSetting("username") == "":
        raise SettingsExceptions(language(32012))
    elif settings.getSetting("api_key") == "":
        raise SettingsExceptions(language(32013))
    return True


def is_settings_okey(daemon=False, silent=False):
    """ Check if we have username and api key? """
    if settings.getSetting("username") == "" and settings.getSetting("api_key") == "":
        if silent:
            return False
        elif daemon:
            notification(__name__, language(32014))
        else:
            xbmcgui.Dialog().ok(__name__, language(32014))
        return False

    elif settings.getSetting("username") == "":
        if silent:
            return False
        if daemon:
            notification(__name__, language(32012))
        else:
            xbmcgui.Dialog().ok(__name__, language(32012))
        return False

    elif settings.getSetting("api_key") == "":
        if silent:
            return False
        if daemon:
            notification(__name__, language(32013))
        else:
            xbmcgui.Dialog().ok(__name__, language(32013))
        return False

    return True


def not_seen_movie(imdb, array):
    for x in array:
        if imdb == x['imdb_id']:
            return False
    return True

def seen_movie(imdb, array_of_movies):
    for movie in array_of_movies:
        if imdb == movie['imdb_id']:
            return True
    return False


def seen_episode(e, array):
    for i in range(0, len(array)):
        if e == array[i]:
            return True
    return False


def is_not_in(test, array):
    for x in array:
        if test in x:
            return False
    return True


def to_seconds(timestr):
    seconds = 0
    for part in timestr.split(':'):
        seconds = seconds * 60 + int(part)
    return seconds
