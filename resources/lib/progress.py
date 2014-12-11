import xbmcgui

__title__ = "EpisodeHunter"


def create(msg):
    progress = xbmcgui.DialogProgress()
    progress.create(__title__, msg)
    return progress
