import functools

BASE_URL = 'http://todoable.teachable.tech/api'
DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
TOKEN_TTL = 20 * 60  # seconds

TIMEOUT = 2  # seconds


class ToDoableException(Exception):
    pass


class BadResponse(ToDoableException):
    """
    Bad response from the server was received
    """


class TimeoutException(ToDoableException):
    """
    Timeout encountered after a request has been made
    """


class AuthenticationError(ToDoableException):
    """
    Authentication problem encountered
    """


class MalformedResponseException(ToDoableException):
    """
    A response has been received, but with an unexpected payload
    """


class InternalServerException(ToDoableException):
    """
    A server problem on the Todoable server side.
    """


class InvalidRequestException(ToDoableException):
    """
    Invalid request made.
    """


class RateLimitException(ToDoableException):
    """
    Too many requests made.
    """


class NotFoundException(ToDoableException):
    """
    Object not found
    """

def handle_malformed_response(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except KeyError:
            raise MalformedResponseException(
                "Error initializing %s instance with data: %s" % (args[0], args[1]))
    return wrapper
