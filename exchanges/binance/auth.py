from urllib.parse import urlencode
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Dict
from urllib.parse import urlencode
import requests
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo


BASE_URL = 'https://api.binance.com'
ONE_MINUTE = 60


def get_timestamp():
    return int(time.time() * 1000)


class BinanceAuth:
    def __init__(self, api_key: str, api_secret: str):
        self.__API_KEY = api_key
        self.__API_SECRET = api_secret

    # used for sending request requires the signature
    @on_exception(expo, RateLimitException, max_tries=10)
    @limits(calls=20, period=ONE_MINUTE)
    def send_signed_request(self, http_method, url_path, payload=None):
        if payload is None:
            payload = {}
        query_string = urlencode(payload, True)
        if query_string:
            query_string = "{}&timestamp={}".format(query_string, get_timestamp())
        else:
            query_string = 'timestamp={}'.format(get_timestamp())

        url = BASE_URL + url_path + '?' + query_string + '&signature=' + self.__hashing(query_string)
        print("{} {}".format(http_method, url))
        params = {'url': url, 'params': {}}
        response = self.__dispatch_request(http_method)(**params)
        return response.json()

    # used for sending public data request
    @on_exception(expo, RateLimitException, max_tries=10)
    @limits(calls=20, period=ONE_MINUTE)
    def send_public_request(self, url_path, payload=None):
        if payload is None:
            payload = {}
        query_string = urlencode(payload, True)
        url = BASE_URL + url_path
        if query_string:
            url = url + '?' + query_string
        print("{}".format(url))
        response = self.__dispatch_request('GET')(url=url)
        return response.json()

    def __hashing(self, query_string):
        return hmac.new(self.__API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def __dispatch_request(self, http_method):
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json;charset=utf-8',
            'X-MBX-APIKEY': self.__API_KEY
        })
        return {
            'GET': session.get,
            'DELETE': session.delete,
            'PUT': session.put,
            'POST': session.post,
        }.get(http_method, 'GET')