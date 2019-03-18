import copy
import datetime
import mock
import json
import uuid
import requests
import unittest

from todoable.api import ToDoableClient
from todoable.lib import (
    AuthenticationError,
    BASE_URL,
    InvalidRequestException,
    NotFoundException,
    RateLimitException,
    InternalServerException,
    ToDoableException,
    TOKEN_TTL,
)
from todoable.models import List, ListItem
from util import create_object_fixture


class ClientTest(unittest.TestCase):

    def setUp(self):
        self.client = self._create_client()

    @mock.patch('todoable.api.ToDoableClient.get_token')
    def _create_client(self, get_token_mock):
        get_token_mock.return_value = "abcdef", datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_TTL)
        return ToDoableClient.from_creds("user", "pw")

    @mock.patch('todoable.api.requests.post')
    def test_from_creds_bad(self, post_mock):
        resp_mock = mock.Mock()
        resp_mock.status_code = 401
        post_mock.return_value = resp_mock
        with self.assertRaises(AuthenticationError):
            ToDoableClient.from_creds("bad_user", "bad_pw")

    @mock.patch('todoable.api.requests.get')
    def test_make_request_ok(self, get_mock):
        get_mock.return_value.status_code = 200
        self.client.make_request(requests.get, '')
        get_mock.assert_called_once()

    @mock.patch('todoable.api.requests.get')
    def test_make_request_bad(self, get_mock):

        for (status_codes, expected_exception) in [
            [(401, ), AuthenticationError],
            [(400, 422), InvalidRequestException],
            [(404, ), NotFoundException],
            [(429, ), RateLimitException],
            [(500, ), InternalServerException],
            [(600, ), ToDoableException]
        ]:
            for status_code in status_codes:
                resp_mock = mock.Mock()
                resp_mock.status_code = status_code
                get_mock.return_value = resp_mock
                with self.assertRaises(expected_exception):
                    self.client.make_request(requests.get, '')

    @mock.patch('todoable.api.requests.get')
    @mock.patch('todoable.api.ToDoableClient.update_token')
    def test_refresh_token(self, update_token_mock, get_mock):
        self.client._token_expiry = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)

        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        get_mock.return_value = resp_mock
        self.client.make_request(requests.get, '')
        update_token_mock.assert_called_once()

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_get_lists(self, mr_mock):
        id_ = str(uuid.uuid4())
        name = 'my list'
        src = "%s/lists/%s" % (BASE_URL, id_)

        mock_json = {
            'lists': [create_object_fixture(id_, name, src)]
        }

        mocked_response = mock.Mock()
        mocked_response.json.return_value = mock_json
        mr_mock.return_value = mocked_response
        self.assertEqual(mock_json, self.client.get_lists(raw=True))

        list_ = self.client.get_lists()[0]
        self.assertIsInstance(list_, List)
        serialized_list = copy.copy(list_.__dict__)
        serialized_list.pop('items')
        self.assertDictEqual(serialized_list, mock_json['lists'][0])

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_create_list(self, mr_mock):

        id_ = str(uuid.uuid4())
        name = 'my list'
        src = "%s/lists/%s" % (BASE_URL, id_)

        mock_json = create_object_fixture(id_, name, src)
        mocked_response = mock.Mock()
        mocked_response.json.return_value = mock_json
        mr_mock.return_value = mocked_response
        self.assertEqual(mock_json, self.client.create_list(name, raw=True))

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_update_list(self, mr_mock):

        list_id = str(uuid.uuid4())
        new_name = 'updated list name'

        self.client.update_list(list_id, new_name)

        mr_mock.assert_called_once_with(
            requests.patch,
            "%s/%s/%s" % (BASE_URL, 'lists', list_id),
            data=json.dumps({'list': {'name': new_name}})
        )

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_delete_list(self, mr_mock):

        list_id = 'list to be deleted'
        self.client.delete_list(list_id)

        mr_mock.assert_called_once_with(
            requests.delete,
            "%s/%s/%s" % (BASE_URL, 'lists', list_id)
        )

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_create_list_item(self, mr_mock):

        list_id = str(uuid.uuid4())
        item_name = 'my item'
        item_id = str(uuid.uuid4())
        src = "%s/%s/%s/%s/%s" % (self.client.BASE_URL, 'lists', list_id, 'items', item_id)

        mock_json = create_object_fixture(item_id, item_name, src, item=True)
        mocked_response = mock.Mock()
        mocked_response.json.return_value = mock_json
        mr_mock.return_value = mocked_response

        created = self.client.create_list_item(list_id, item_name)

        self.assertIsInstance(created, ListItem)
        self.assertDictEqual(mock_json, created.__dict__)

        created_raw = self.client.create_list_item(list_id, item_name, raw=True)
        self.assertDictEqual(mock_json, created_raw)

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_delete_list_item(self, mr_mock):

        list_id = 'list name'
        item_id = str(uuid.uuid4())

        self.client.delete_list_item(list_id, item_id)

        mr_mock.assert_called_once_with(
            requests.delete,
            "%s/%s/%s/%s/%s" % (BASE_URL, 'lists', list_id, 'items', item_id)
        )

    @mock.patch('todoable.api.ToDoableClient.make_request')
    def test_complete_list_item(self, mr_mock):

        list_id = 'list name'
        item_id = str(uuid.uuid4())

        self.client.complete_list_item(list_id, item_id)

        mr_mock.assert_called_once_with(
            requests.put,
            "%s/%s/%s/%s/%s/%s" % (BASE_URL, 'lists', list_id, 'items', item_id, 'finish')
        )

    # def _object_fixture(self, id_, name, src, item=False, finished_at=None):
    #
    #     fixture = {
    #         'id': id_,
    #         'name': name,
    #         'src': src
    #     }
    #
    #     if item:
    #         fixture['finished_at'] = finished_at
    #
    #     return fixture