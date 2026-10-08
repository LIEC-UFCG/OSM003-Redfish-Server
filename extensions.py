from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import ENABLE_RATE_LIMIT
import os

RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI")

# Function to get the authentication token from the request header
# If the token is not present, uses the remote address of the client
def get_token():
    """
    Retrieve authentication token from request header.

    If token is not present, use the remote client address instead.

    Returns:
        str: Authentication token or client IP address.
    """
    return request.headers.get("X-Auth-Token") or get_remote_address()

# Configure rate limiter
limiter = Limiter(
    key_func=get_token,
    default_limits=[],
    storage_uri=RATE_LIMIT_STORAGE_URI if RATE_LIMIT_STORAGE_URI else "memory://"
)

def conditional_limit(limit):
    def decorator(func):
        if ENABLE_RATE_LIMIT:
            return limiter.limit(limit)(func)
        return func
    return decorator