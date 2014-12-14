from mock import patch, Mock
import unittest

from test.xbmc_base_test_case import XbmcBaseTestCase
from test.test_data import eh_movie_result, xbmc_movie_result
from test.mocks import connection_mock
from resources.exceptions import UserAbortExceptions


class GivenMovieSync(XbmcBaseTestCase, object):
    """
    Test class for movie sync methods between EH and XBMC
    """

    xbmc = None
    xbmcgui = None

    def setUp(self):
        super(GivenMovieSync, self).setUp()
        import resources.lib.sync.sync_movies as sync

        self.sync = sync

        self.xbmc.abortRequested = False
        self.progress = Mock()
        self.progress.iscanceled.return_value = False
        self.xbmcgui.DialogProgress = Mock(return_value = self.progress)

    def test_should_return_one_movie(self):
        # Arrange
        connection = connection_mock.ConnectionMock()
        sync = self.sync.Movies(connection)
        sync.xbmc_movies = xbmc_movie_result.get('The Hunger Games', 'The Thing', 'Battleship')
        sync.eh_watched_movies = eh_movie_result.get('The Hunger Games', 'Battleship')
        sync.progress = self.progress

        # Act
        sync.get_movies_to_sync_upstream()

        # Assert
        upstream = sync.upstream_sync
        self.assertEqual(len(upstream), 1)

    def test_should_return_two_movies(self):
        # Arrange
        connection = connection_mock.ConnectionMock()
        sync = self.sync.Movies(connection)
        sync.xbmc_movies = xbmc_movie_result.get('The Hunger Games', 'The Thing', 'Battleship')
        sync.eh_watched_movies = eh_movie_result.get('The Hunger Games')
        sync.progress = self.progress

        # Act
        sync.get_movies_to_sync_upstream()

        # Assert
        upstream = sync.upstream_sync
        self.assertEqual(len(upstream), 2)

    def test_should_return_two_specific_movies(self):
        # Arrange
        connection = connection_mock.ConnectionMock()
        sync = self.sync.Movies(connection)
        sync.xbmc_movies = xbmc_movie_result.get('The Hunger Games', 'The Thing', 'Battleship')
        sync.eh_watched_movies = eh_movie_result.get('The Hunger Games')
        sync.progress = self.progress

        # Act
        sync.get_movies_to_sync_upstream()

        # Assert
        upstream = sync.upstream_sync
        self.assertIn(upstream[0].title, ['The Thing', 'Battleship'])
        self.assertIn(upstream[1].title, ['The Thing', 'Battleship'])
        self.assertNotEqual(upstream[0].title, upstream[1].title)

    def test_should_not_include_movies_that_do_not_have_all_attributes(self):
        # Arrange
        connection = connection_mock.ConnectionMock()
        sync = self.sync.Movies(connection)
        sync.xbmc_movies = xbmc_movie_result.get('The Hunger Games') + xbmc_movie_result.get('The Thing', remove_attr='year')
        sync.eh_watched_movies = []
        sync.progress = self.progress

        # Act
        sync.get_movies_to_sync_upstream()

        # Assert
        upstream = sync.upstream_sync
        self.assertEqual(len(upstream), 1)
        self.assertEqual(upstream[0].title, 'The Hunger Games')

    def test_should_rise_exception_when_abort_is_requested(self):
        connection = connection_mock.ConnectionMock()
        sync = self.sync.Movies(connection)
        sync.xbmc_movies = xbmc_movie_result.get('The Hunger Games')
        sync.eh_watched_movies = []
        sync.progress = self.progress
        self.xbmc.abortRequested = True

        with self.assertRaises(SystemExit):
            sync.get_movies_to_sync_upstream()

    def test_should_rise_exception_when_canceled_is_requested(self):
        connection = connection_mock.ConnectionMock()
        sync = self.sync.Movies(connection)
        sync.xbmc_movies = xbmc_movie_result.get('The Hunger Games')
        sync.eh_watched_movies = []
        self.progress.iscanceled.return_value = True
        sync.progress = self.progress

        with self.assertRaises(UserAbortExceptions):
            sync.get_movies_to_sync_upstream()

    def test_should_return_fasle_if_movie_has_no_imdb_id(self):
        movie = xbmc_movie_result.get('The Hunger Games', remove_attr=['imdbnumber'])[0]
        result = self.sync.movie_criteria(movie)
        self.assertFalse(result)

    def test_should_return_fasle_if_movie_has_no_title_nor_orginaltitle(self):
        movie = xbmc_movie_result.get('The Hunger Games', remove_attr=['title', 'originaltitle'])[0]
        result = self.sync.movie_criteria(movie)
        self.assertFalse(result)

    def test_should_return_true_if_movie_has_no_title_but_orginaltitle(self):
        movie = xbmc_movie_result.get('The Hunger Games', remove_attr=['title'])[0]
        result = self.sync.movie_criteria(movie)
        self.assertTrue(result)

    def test_should_return_true_if_movie_has_no_orginaltitle_but_title(self):
        movie = xbmc_movie_result.get('The Hunger Games', remove_attr=['originaltitle'])[0]
        result = self.sync.movie_criteria(movie)
        self.assertTrue(result)

    def test_should_return_false_if_movie_has_no_year(self):
        movie = xbmc_movie_result.get('The Hunger Games', remove_attr=['year'])[0]
        result = self.sync.movie_criteria(movie)
        self.assertFalse(result)

    def test_should_return_false_if_movie_has_year_but_its_zero(self):
        movie = xbmc_movie_result.get('The Hunger Games')[0]
        movie['year'] = 0
        result = self.sync.movie_criteria(movie)
        self.assertFalse(result)

    def test_should_return_false_if_movie_has_no_play_count(self):
        movie = xbmc_movie_result.get('The Hunger Games', remove_attr=['playcount'])[0]
        result = self.sync.movie_criteria(movie)
        self.assertFalse(result)

    def test_should_return_false_if_movie_has_play_count_but_its_zero(self):
        movie = xbmc_movie_result.get('The Hunger Games')[0]
        movie['playcount'] = 0
        result = self.sync.movie_criteria(movie)
        self.assertFalse(result)




if __name__ == '__main__':
    unittest.main()
