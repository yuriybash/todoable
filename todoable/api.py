import json
import logging
import requests
import sys
from datetime import datetime
from dateutil import parser

from lib import (
    AuthenticationError,
    BASE_URL,
    DEFAULT_HEADERS,
    InternalServerException,
    InvalidRequestException,
    NotFoundException,
    RateLimitException,
    TIMEOUT,
    TimeoutException,
    TOKEN_TTL,
    ToDoableException
)
from models import List, ListItem

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)


class ToDoableClient(object):

    HEADERS = DEFAULT_HEADERS
    BASE_URL = BASE_URL

    def __init__(self, token, token_expiry, username=None, password=None):
        """
        Initialize a ToDoableClient with a token, token_expiry, and (optional)
        username/pw. If username/pw isn't provided, automatic reauthentication
        is not possible.

        :param token: the token
        :type token: basestring
        :param token_expiry: token expiration date
        :type token_expiry: datetime.datetime
        :param username: username
        :type username: basestring
        :param password: password
        :type password: basestring
        """
        self._token = token
        self._token_expiry = token_expiry
        self._username = username
        self._password = password

        if not (self._username and self._password):
            log.warning(
                "Tokens expire after %d seconds, username/pw required for "
                "automatic reauthentication" % TOKEN_TTL
            )

        self.HEADERS.update({'Authorization': 'Token token=%s' % self._token})

    @classmethod
    def from_creds(cls, username, password):
        """
        Initialize a client from a username and password. Gets and sets a token

        :param username: username
        :type username: basestring
        :param password: password
        :type password: basestring
        :return: the ToDoableClient instance
        :rtype: ToDoableClient
        """
        token, expiry = cls.get_token(username, password)
        return cls(token, expiry, username=username, password=password)

    @classmethod
    def from_token(cls, token, token_expiry, username=None, password=None):
        """
        Initialize a client from a token/token_expiry. Useful if you already
        have a token and can reuse it.

        :param token: the token
        :type token: basestring
        :param token_expiry: token expiration date
        :type token_expiry: datetime.datetime
        :param username: username
        :type username: basestring
        :param password: password
        :type password: basestring
        :return: ToDoableClient instance
        :rtype: ToDoableClient
        """
        return cls(
            token,
            token_expiry=token_expiry,
            username=username,
            password=password
        )

    @classmethod
    def get_token(cls, username, password):
        """
        Get a new token, given a username/pw.

        :param username: username
        :type username: basestring
        :param password: password
        :type password: basestring
        :return: token payload and expiration date
        :rtype token: (basestring, datetime.datetime[tz-unaware])
        """
        url = "%s/%s" % (cls.BASE_URL, 'authenticate')
        resp = requests.post(
            url,
            auth=(username, password),
            headers=cls.HEADERS,
            timeout=TIMEOUT
        )

        if resp.status_code == 401:
            raise AuthenticationError("Unable to authenticate with given username/pw")
        body = resp.json()
        token, expiry = body['token'], parser.parse(body['expires_at']).replace(tzinfo=None)
        return token, expiry

    def update_token(self):
        if not (self._username and self._password):
            raise AuthenticationError("Unable to update token without username and password")
        self._token, self._token_expiry = self.get_token(self._username, self._password)

    def make_request(self, func, url, headers=None, data=None):
        """
        Make a request.

        :param func: request-making function
        :type func: callable
        :param url: url
        :type url: basestring
        :param headers: headers to use. if `None`, default headers are used
        :type headers: dict
        :param data: data to be sent
        :type data: basestring (serialized json)
        :return: the response
        :rtype: requests.models.Response
        """

        def _handle_error(bad_resp):
            """
            Handle non 2xx response. Raises appropriate exception.

            :param bad_resp: the response
            :type bad_resp: requests.models.Response
            :return: None
            :rtype: None
            """
            if bad_resp.status_code == 401:
                exception, msg = AuthenticationError, "Error authenticating"
            elif bad_resp.status_code == 404:
                exception, msg = NotFoundException, "Object not found"
            elif bad_resp.status_code in (400, 422):
                exception, msg = InvalidRequestException, "Malformed request made"
            elif bad_resp.status_code == 429:
                exception, msg = RateLimitException, "Too many requests"
            elif 500 <= bad_resp.status_code <= 599:
                exception, msg = InternalServerException, "Internal Server exception raised"
            else:
                exception, msg = ToDoableException, "Error reached while making request"

            raise exception(
                "%s, status code %s received, body: %s" %
                (msg, bad_resp.status_code, bad_resp.text)
            )

        if not self._token or self._token_expiry and datetime.utcnow() >= self._token_expiry:
            self.update_token()

        try:
            resp = func(url, headers=headers or self.HEADERS, data=data, timeout=TIMEOUT)
        except requests.ConnectionError:
            raise TimeoutException("Timed out while making request")

        if not 200 <= resp.status_code <= 299:
            _handle_error(resp)
        return resp

    def get_lists(self, raw=False, include_items=False):
        """
        Get lists.

        :param raw: whether to return raw response body
        :type raw: bool
        :param include_items: whether to include items associated with list
        :type include_items: bool
        :return: the lists, either raw or model instances
        :rtype: [dict] | [List]
        """
        url = "%s/%s" % (self.BASE_URL, 'lists')
        serialized = self.make_request(requests.get, url).json()

        if raw:
            return serialized

        lists = [List.from_dict(l) for l in serialized['lists']]
        if include_items:
            for todo_list in lists:
                items = self.get_list(todo_list.id, raw=True)['items']
                todo_list.items = [ListItem.from_dict(i) for i in items]
        return lists

    def create_list(self, list_name, raw=False):
        """
        Create a list.

        :param list_name: list name
        :type list_name: basestring
        :param raw: whether to return raw response body
        :type raw: bool
        :return: the list, either raw or model instance
        :rtype: dict | List
        """
        url = "%s/%s" % (self.BASE_URL, 'lists')

        data = {
            "list": {
                "name": list_name
            }
        }

        serialized = self.make_request(requests.post, url, data=json.dumps(data)).json()

        return serialized if raw else List.from_dict(serialized)

    def get_list(self, list_id, raw=False):
        """
        Get a list by ID.

        :param raw: whether to return raw response body
        :type raw: bool
        :return: the list, either raw or model instances
        :rtype: dict | List
        """
        url = "%s/%s/%s" % (self.BASE_URL, 'lists', list_id)
        serialized = self.make_request(requests.get, url).json()
        serialized.update({'id': list_id})

        if raw:
            return serialized

        return List.from_dict(
            serialized,
        )

    def update_list(self, list_id, new_name):
        """
        Update a list.

        :param list_id: list ID
        :type list_id: basestring
        :param new_name: new name for the list
        :type new_name: basestring
        :return: None
        :rtype: None
        """

        url = "%s/%s/%s" % (self.BASE_URL, 'lists', list_id)
        data = {
            "list": {
                "name": new_name
            }
        }
        self.make_request(requests.patch, url, data=json.dumps(data))

    def delete_list(self, list_id):
        """
        Delete a list.

        :param list_id: list ID
        :type list_id: basestring
        :return: None
        :rtype: None
        """

        url = "%s/%s/%s" % (self.BASE_URL, 'lists', list_id)
        self.make_request(requests.delete, url)

    def create_list_item(self, list_id, item_name, raw=False):
        """
        Create an item associated with a list.

        :param list_id: list ID
        :type list_id: basestring
        :param item_name: item name
        :type item_name: basestring
        :param raw: whether to return raw response body
        :type raw: bool
        :return: raw item or model instance
        :rtype: dict | ListItem
        """
        url = "%s/%s/%s/%s" % (self.BASE_URL, 'lists', list_id, 'items')

        data = {
            "item": {
                "name": item_name
            }
        }

        serialized = self.make_request(requests.post, url, data=json.dumps(data)).json()
        if raw:
            return serialized
        return ListItem.from_dict(serialized)

    def complete_list_item(self, list_id, item_id):
        """
        Complete a list item.

        :param list_id: list ID
        :type list_id: basestring
        :param item_id: item ID
        :type item_id: basestring
        :return: None
        :rtype: None
        """
        url = "%s/%s/%s/%s/%s/%s" % (self.BASE_URL, 'lists', list_id, 'items', item_id, 'finish')
        self.make_request(requests.put, url)

    def delete_list_item(self, list_id, item_id):
        """
        Delete a list item.

        :param list_id: list ID
        :type list_id: basestring
        :param item_id: item ID
        :type item_id: basestring
        :return: None
        :rtype: None
        """
        url = "%s/%s/%s/%s/%s" % (self.BASE_URL, 'lists', list_id, 'items', item_id)
        self.make_request(requests.delete, url)
