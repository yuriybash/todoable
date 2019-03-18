from dateutil import parser
import abc

from lib import handle_malformed_response, MalformedResponseException


class ToDoableObject(object):
    """
    Base class for all ToDoable objects
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def from_dict(self, *args, **kwargs):
        """
        Create an instance of a ToDoableObject subclass from an API response
        """

    def __repr__(self):
        attrs = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return "<%s: {%s}>" % (self.__class__.__name__, ', '.join(attrs))


class List(ToDoableObject):

    def __init__(self, name, id=None, items=None, src=None):
        """
        Initialize a List object. Note that `items` may be `None` because they
        haven't been loaded, though they do exist.

        :param name: list name
        :type name: basestring
        :param id: list ID
        :type id: basestring
        :param items: items associated with the list.
        :type items: None | [ListItem]
        :param src: src URL
        :type src: basestring
        """
        self.name = name
        self.id = id
        self.items = items
        self.src = src

    @classmethod
    @handle_malformed_response
    def from_dict(cls, dict_):
        """
        Initialize a List from a server response.

        :param dict_: dict repr. of a server response
        :type dict_: dict
        :return: List instance
        :rtype: List
        """

        items = None
        if dict_.get('items'):
            items = [ListItem.from_dict(i_dict) for i_dict in dict_['items']]

        return cls(
            dict_['name'],
            id=dict_['id'],
            src=dict_.get('src'),
            items=items
        )


class ListItem(ToDoableObject):

    def __init__(self, name, id=None, src=None, finished_at=None):
        """
        Initialize a ListItem.

        :param name: list name
        :type name: basestring
        :param id: list ID
        :type id: basestring
        :param src: src URL
        :type src: basestring
        :param finished_at: completion time of the item, if any
        :type finished_at: None | datetime.datetime (tz-unaware)
        """

        self.name = name
        self.id = id
        self.src = src
        self.finished_at = finished_at

    @classmethod
    @handle_malformed_response
    def from_dict(cls, dict_):
        """
        Initialize a ListItem from a server response.

        :param dict_: dict repr. of a server response
        :type dict_: dict
        :return: ListItem instance
        :rtype: ListItem
        """

        finished_at = None
        if dict_['finished_at']:
            finished_at = parser.parse(dict_['finished_at']).replace(tzinfo=None)

        return cls(
            dict_['name'],
            dict_['id'],
            dict_['src'],
            finished_at
        )

