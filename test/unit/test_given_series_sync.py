from mock import Mock
import unittest

from test.xbmc_base_test_case import XbmcBaseTestCase
from test.test_data import xbmc_series_result

class GivenSeriesSync(XbmcBaseTestCase, object):
    """
    Test class for series sync methods between EH and XBMC
    """

    xbmc = None
    xbmcgui = None

    def setUp(self):
        super(GivenSeriesSync, self).setUp()
        import resources.lib.sync.sync_series as sync

        self.sync = sync

        self.xbmc.abortRequested = False
        self.progress = Mock()
        self.progress.iscanceled.return_value = False
        self.xbmcgui.DialogProgress = Mock(return_value=self.progress)

    def test_should_return_true_if_series_is_valid(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertTrue(result)

    def test_should_return_fasle_if_series_has_no_title(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1)
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]
        tv_shows.pop('title', None)

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertFalse(result)

    def test_should_return_fasle_if_series_has_no_tvdb_id(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]
        tv_shows.pop('imdbnumber', None)

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertFalse(result)

    def test_should_return_false_if_series_has_no_year(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]
        tv_shows.pop('year', None)

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertFalse(result)

    def test_should_return_false_if_series_has_year_but_it_is_zero(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]
        tv_shows['year'] = 0

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertFalse(result)

    def test_should_return_false_if_series_has_no_play_count(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]
        tv_shows.pop('playcount', None)

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertFalse(result)

    def test_should_return_true_if_series_has_play_count_event_if_its_zero(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        series_mock.add_episodes(1, 1, xbmc_series_result.EPISODE)
        tv_shows = series_mock.get_tv_shows()[0]
        tv_shows['playcount'] = 0

        # Act
        result = self.sync.series_criteria(tv_shows, series_mock.get_episodes(tv_shows, 1))

        # Assert
        self.assertTrue(result)

    def test_should_return_false_if_some_episode_is_missing_episode(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        tv_shows = series_mock.get_tv_shows()[0]
        episodes = [{
            'season': 1,
            'playcount': 1
        }]

        # Act
        result = self.sync.series_criteria(tv_shows, episodes)

        # Assert
        self.assertFalse(result)

    def test_should_return_false_if_some_episode_is_missing_season(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        tv_shows = series_mock.get_tv_shows()[0]
        episodes = [{
            'episode': 1,
            'playcount': 1
        }]

        # Act
        result = self.sync.series_criteria(tv_shows, episodes)

        # Assert
        self.assertFalse(result)

    def test_should_return_false_if_some_episode_is_missing_playcount(self):
        # Arrange
        series_mock = xbmc_series_result.TvShows()
        series_mock.add_show(tvshowid=1, title='Dexter')
        tv_shows = series_mock.get_tv_shows()[0]
        episodes = [{
            'episode': 1,
            'season': 1
        }]

        # Act
        result = self.sync.series_criteria(tv_shows, episodes)

        # Assert
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
