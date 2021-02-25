# Create custom authentication for Coinbase API
import hashlib
import hmac
import time

from requests.utils import to_native_string
from requests.auth import AuthBase


class CoinbaseWalletAuth(AuthBase):
    def __init__(self, api_key, secret_key, api_version: str = "2021-02-18"):
        self.__api_key = api_key
        self.__api_secret_key = secret_key
        self.__api_version = api_version

    def __call__(self, request):
        timestamp = str(int(time.time()))
        message = timestamp + request.method + request.path_url + (request.body or '')
        secret = self.__api_secret_key

        if not isinstance(message, bytes):
            message = message.encode()
        if not isinstance(secret, bytes):
            secret = secret.encode()

        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        request.headers.update({
            to_native_string('CB-VERSION'): self.__api_version,
            to_native_string('CB-ACCESS-KEY'): self.__api_key,
            to_native_string('CB-ACCESS-SIGN'): signature,
            to_native_string('CB-ACCESS-TIMESTAMP'): timestamp,
        })
        return request