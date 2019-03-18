from dateutil import parser
import unittest
import uuid

from todoable.lib import BASE_URL, MalformedResponseException
from todoable.models import List, ListItem
from util import create_object_fixture


class ListTest(unittest.TestCase):

    def test_list_init(self):
        name, id_ = 'first_list', str(uuid.uuid4())
        list_ = List(name, id=id_)
        self.assertIsInstance(list_, List)
        self.assertEqual(list_.name, name)
        self.assertEqual(list_.id, id_)

    def test_list_from_dict_ok(self):
        name = "second_list"
        id_ = str(uuid.uuid4())
        src = "%s/lists/%s" % (BASE_URL, id_)

        list_ = List.from_dict(
            create_object_fixture(id_, name, src)
        )

        self.assertEqual(name, list_.name)
        self.assertEqual(id_, list_.id)
        self.assertEqual(id_, list_.id)
        self.assertEqual(src, list_.src)

    def test_list_from_dict_bad(self):
        with self.assertRaises(MalformedResponseException):
            List.from_dict({"abc": "def"})


class ListItemTest(unittest.TestCase):

    def list_item_init(self):

        name = 'first list item'
        id_ = str(uuid.uuid4())
        item = ListItem(name, id=id_)
        self.assertIsInstance(item, ListItem)
        self.assertEqual(id_, item.id)
        self.assertEqual(name, item.name)

    def test_list_item_from_dict_ok(self):

        name = "second list item"
        id_ = str(uuid.uuid4())
        src = "%s/lists/%s/items/%s" % (BASE_URL, str(uuid.uuid4()), id_)
        finished_at = '2019-03-16T16:28:48.550Z'

        item = ListItem.from_dict(
            create_object_fixture(id_, name, src, item=True, finished_at=finished_at)
        )

        self.assertIsInstance(item, ListItem)
        self.assertEqual(name, item.name)
        self.assertEqual(id_, item.id)
        self.assertEqual(src, item.src)
        self.assertEqual(
            parser.parse(finished_at).replace(tzinfo=None), item.finished_at
        )

    def test_list_item_from_dict_bad(self):

        with self.assertRaises(MalformedResponseException):
            ListItem.from_dict({})
