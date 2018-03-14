import unittest
import json
from mock import MagicMock, call
from test.xbmc_base_test_case import XbmcBaseTestCase


class GivenXbmcHelper(XbmcBaseTestCase, object):

    json_rcp_mock = None
    helper = None

    def setUp(self):
        super(GivenXbmcHelper, self).setUp()
        self.xbmc.executeJSONRPC = self.json_rcp_mock = MagicMock()
        import resources.lib.xbmc_repository
        self.helper = resources.lib.xbmc_repository

    def test_should_get_active_player(self):
        # Arrange
        response = json.dumps({'result': [{'playerid': 5}]})
        self.json_rcp_mock.return_value = response

        # Act
        result = self.helper.active_player()

        # Assert
        self.assertEqual(result, 5)

    def test_should_get_watched_shows(self):
        # Arrange
        response = [
            json.dumps(
                {'result': {'tvshows': [
                    {'title': 'Dexter', 'imdbnumber': '12345', 'year': 2006}
                ]}}
            ),
            json.dumps(
                {'result': {'tvshows': [
                    {'title': 'Breaking Bad', 'imdbnumber': '54321', 'year': 2010}
                ]}}
            ),
            json.dumps(
                {'result': {'tvshows': []}}
            )
        ]
        self.json_rcp_mock.side_effect = response

        # Act
        result = self.helper.watched_shows()

        # Assert
        num_show = sum(1 for x in result)
        args_list = self.json_rcp_mock.call_args_list
        self.assertEqual(num_show, 2)
        self.assertEqual(self.json_rcp_mock.call_count, 3)


if __name__ == '__main__':
    unittest.main()
