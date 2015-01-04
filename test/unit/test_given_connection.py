from mock import patch, Mock
import unittest
import json

from test.xbmc_base_test_case import XbmcBaseTestCase
from resources.model import movie_model
from test.test_data import xbmc_movie_result


class GivenConnection(XbmcBaseTestCase, object):
    """
    Test class for connections
    """

    xbmc = None
    xbmcgui = None
    http_mock = None
    http = Mock()

    def setUp(self):
        super(GivenConnection, self).setUp()
        self.import_resurse()

    def import_resurse(self):
        import resources.lib.connection.connection as connection
        self.connection = connection.Connection(self.http)

    @patch('resources.lib.helper.get_username', lambda: "username")
    @patch('resources.lib.helper.get_api_key', lambda: "key")
    def test_should_send_a_post_request_to_eh(self):
        movies = [movie_model.create_from_xbmc(m) for m in xbmc_movie_result.get('The Hunger Games')]

        self.connection.set_movies_watched(movies)

        self.http.make_request.assert_called_once_with('/v2/movie/watched', '{"username": "username", "movies": [{"plays": 3, "last_played": 1412964211, "title": "The Hunger Games", "xbmc_id": "1", "imdb_id": "tt1392170", "year": "2011"}], "apikey": "key"}')

if __name__ == '__main__':
    unittest.main()
