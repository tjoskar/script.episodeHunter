from mock import patch, Mock
import unittest

from xbmc_base_test_case import XbmcBaseTestCase
from test_data import eh_movie_result, xbmc_movie_result
from mocks import connection_mock


class GivenMovieSync(XbmcBaseTestCase, object):
    """
    Test class for movie sync methods between EH and XBMC
    """

    xbmc = None
    xbmcgui = None

    def setUp(self):
        super(GivenMovieSync, self).setUp()
        import resources.lib.sync as sync
        self.sync = sync

        self.progress = Mock()
        self.xbmcgui.DialogProgress = Mock(return_value=self.progress)

    @patch('resources.lib.xbmc_helper.get_movies_from_xbmc')
    def test_shuld_upload_one_movie(self, xbmc_helper_mock):
        # Arrange
        connection = connection_mock.ConnectionMock(
            watched_movies=eh_movie_result.get('The Hunger Games', 'The Thing'),
            return_status_code=200
        )
        xbmc_helper_mock.return_value = xbmc_movie_result.get('The Hunger Games', 'The Thing', 'Battleship')
        self.xbmc.abortRequested = False

        # Act
        sync = self.sync.SyncMovies(connection)
        sync.sync()

        # Assert
        movie_to_upload = connection.called['set_movies_watched'][0]

        self.assertEqual(len(movie_to_upload), 1, 'Should have uploaded one movie')
        self.assertEqual(len(connection.called['set_movies_watched']), 1, 'set_movies_watched should have been called once')

    @patch('resources.lib.xbmc_helper.get_movies_from_xbmc')
    def test_shuld_upload_two_movies(self, xbmc_helper_mock):
        # Arrange
        connection = connection_mock.ConnectionMock(
            watched_movies=eh_movie_result.get('The Hunger Games'),
            return_status_code=200
        )
        xbmc_helper_mock.return_value = xbmc_movie_result.get('The Hunger Games', 'The Thing', 'Battleship')
        self.xbmc.abortRequested = False

        # Act
        sync = self.sync.SyncMovies(connection)
        sync.sync()

        # Assert
        movie_to_upload = connection.called['set_movies_watched'][0]

        self.assertEqual(len(movie_to_upload), 2, 'Should have uploaded two movies')
        self.assertEqual(len(connection.called['set_movies_watched']), 1, 'set_movies_watched should have been called once')

    @patch('resources.lib.xbmc_helper.get_movies_from_xbmc')
    def test_shuld_upload_battleship(self, xbmc_helper_mock):
        # Arrange
        connection = connection_mock.ConnectionMock(
            watched_movies=eh_movie_result.get('The Hunger Games', 'The Thing'),
            return_status_code=200
        )
        xbmc_helper_mock.return_value = xbmc_movie_result.get('The Hunger Games', 'The Thing', 'Battleship')
        self.xbmc.abortRequested = False

        # Act
        sync = self.sync.SyncMovies(connection)
        sync.sync()

        # Assert
        movie_to_upload = connection.called['set_movies_watched'][0]

        self.assertEqual(movie_to_upload[0].title, 'Battleship', 'Should have uploaded Battleship')

    @patch('resources.lib.xbmc_helper.get_movies_from_xbmc')
    def test_shuld_close_progressbar_when_result_is_none(self, xbmc_helper_mock):
        connection = Mock()
        connection.get_watched_movies.return_value = None
        xbmc_helper_mock.return_value = None

        sync = self.sync.SyncMovies(connection)
        sync.sync()

        self.progress.close.assert_called_once_with()

        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
