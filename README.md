## Approach

### Structure

`todoable/todoable` contains the library code. `api` exposes a single class, `ToDoableCLient`, that offers interfaces to the required endpoints/actions:

- `from_creds`
- `from_token`
- `get_token`
- `make_request` - utility method used by other methods. also generally useful in client libs when specific endpoints/actions aren't supported by the client lib.
- `get_lists`
- `create_list`
- `update_list`
- `delete_list`
- `create_list_item`
- `complete_list_item`
- `delete_list_item`

`lib` - various utilities (custom exceptions, constants, etc)

`models` - contains models for `List` and `ListItem` (more on this later)

### Installation

You can run it without installing using a simple import after opening python/ipdb in `todoable`:

```
python
from todoable.api import ToDoableClient
```

or you can install it (create a virtualenv first):

```
python setup.py install
```

you then have access to the `todoable` lib regardless of dir.

### Usage

A client is instantiated either from credentials provided, e.g.

`client = ToDoableClient.from_creds("my_username", "my_password")`

or from an existing token, if one is available:

`client = ToDoableClient.from_token("MY_TOKEN")`

You then perform standard operations through the `client` (e.g. `client.get_lists()`).

If a username/password is provided (through either method), reauthentication automatically occurs when the token expires. Note that here, we trust the stated token expiry, but in a prod system, we'd probably try updating the token at least once in the face of auth issues.

In addition to the arguments needed for standard CRUD operations, e.g. `client.create_list` accepts `list_name`, most methods also accept the **raw** argument:

`def create_list(self, list_name, raw=False)`

if `raw` is set to False, the method returns an instance of either a `List` or `ListItem`, which are models defined in `models.py` and are objects which encapsulates a list and list item, respectively.

They are thin models and mostly just contain the attributes that each type of object contains, but I've included these for a few reasons:

1. extensibility - in a real life-scenario, more methods would probably exist (e.g. `add_item` on a `List`)
2. deserialization convenience - it does it for you

There's also one other convenient feature using this method: you can include _associated items_ in some requests. For example, if you call:

`client.get_lists(include_items=True)`,

it will return the items associated with each list as well:

```
client.get_lists(include_items=True)
# <List: {items = [<ListItem: {finished_at = None, src = u'http://todoable.teachable.tech/api/lists/504d28bc-2148-4751-bea3-472993f3a6f9/items/acf9733c-e15e-429d-9b47-160a7b2f1b86', name = u'new item for list 3', id = u'acf9733c-e15e-429d-9b47-160a7b2f1b86'}>], src = u'http://todoable.teachable.tech/api/lists/504d28bc-2148-4751-bea3-472993f3a6f9', name = u'list_name_1', id = u'504d28bc-2148-4751-bea3-472993f3a6f9'}>
```


NB 1: in a real life scenario, you have to consider what happens if _some_ subsequent requests fail (e.g. if you can only load 1/2 the associated items) - what's the expected behavior there?

NB 2: alternatively, these could have been `namedtuple`s.

Typical usage looks something like:

```
client = TodoableClient.from_creds("yuriybash@gmail.com", "mypassword")
lists = client.get_lists()
# list[0] = <List: {items = None, src = u<SRC>, name = u<NAME>, id = u<ID>}>
```


If `raw` is set to True, a dict is constructed from the response and returned.

## Error handling

Error handling is included for both (some) expected exceptions and bad responses. See `todoable/lib` for the custom exceptions that can get raised. I included support for some status codes I didn't see but would expect to normally (e.g. 429 - I tried to get rate limited a bit but didn't want to be too rude :))

The status code and response body is returned in all cases of non-2xx responses.

A (generous) timeout of 2 seconds is used throughout.

I also considered adding custom exceptions for failure to create/update/delete/get items (e.g. `ListUpdateFailed`), but the networking exceptions included provide, in my opinion, sufficient visibility into any problems that occur. Again, this can be up for debate.

## Caveats/Considerations

You can run into situations where, for example, you create a `List` using `client.create_list`, then you update the list separately (a call to `client.update_list`), and then your old `List` object is now out of date. This is a classic example of what happens with ORMs ([example](https://docs.sqlalchemy.org/en/latest/orm/exceptions.html#sqlalchemy.orm.exc.StaleDataError)). Solving this problem requires more effort than is probably expected in a take-home assignment, but it's worth keeping in mind.

I also considered including methods on the aforementioned models such as `.save` or `.update`, but decided against it due to the consideration above. There is actually a somewhat interesting conversation to be had there about the best way to do that, since the model then has to have access to auth information/a client ([example](https://github.com/twitterdev/twitter-python-ads-sdk/blob/master/twitter_ads/creative.py#L55)), and the implementation can get messy if one is not careful. This is why `__init__` on the models uses optional kwargs - for futureproofing in case we want to go down this route later (e.g. an instance is initialized but hasn't been persisted yet).

## Testing

To test, run:

```
python -m unittest tests.test_models
python -m unittest tests.test_client
```

from the root dir. Server responses are mocked out where appropriate.
