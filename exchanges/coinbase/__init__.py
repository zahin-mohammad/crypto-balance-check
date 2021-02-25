import json
import logging
import os
import requests
from typing import Dict
import traceback

from backoff import on_exception, expo
from ratelimit import limits, RateLimitException
from requests import Response

from exchanges.coinbase.auth import CoinbaseWalletAuth
from exchanges.interface import Exchange, Position

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

NAME = 'COINBASE'
BASE_URL = 'https://api.coinbase.com'
LIST_ACCOUNTS = '/v2/accounts'
EXCHANGE_RATES = '/v2/exchange-rates?currency='
SIXTY_MINUTES = 3600


class Coinbase(Exchange):
    def __init__(self):
        super().__init__()
        self.__auth = CoinbaseWalletAuth(
            api_key=os.getenv('COINBASE_API_KEY'),
            secret_key=os.getenv('COINBASE_API_SECRET'))
        logging.info(f"Initialized {self.name()} Exchange")

    def name(self) -> str:
        return NAME

    @on_exception(expo, RateLimitException, max_tries=8)
    @limits(calls=10000, period=SIXTY_MINUTES)
    def call_api(self, method: str, url: str) -> Response:
        return requests.request(method=method, url=url, auth=self.__auth)

    def __get_exchange_rates(self):
        try:
            logging.info(f"{self.name()} GET: {EXCHANGE_RATES+self.fiat}")
            r = self.call_api('GET', BASE_URL + EXCHANGE_RATES + self.fiat)
            return r.json()['data']['rates']
        except Exception as e:
            logging.error(e)
        return {}

    def __get_accounts(self):
        ret = []
        next_uri = LIST_ACCOUNTS
        while next_uri is not None:
            r = {}
            try:
                logging.info(f"{self.name()} GET: {LIST_ACCOUNTS}")
                r = self.call_api('GET', BASE_URL + next_uri)
            except Exception as e:
                traceback.print_exc()
                logging.error(e)

            pagination = r.json()['pagination']
            next_uri = pagination['next_uri']
            data = r.json()['data']
            ret += data
        return ret

    def get_positions(self) -> Dict[str, Position]:
        logging.info(f"{self.name()} get_positions")
        exchange_rates = self.__get_exchange_rates()
        accounts = self.__get_accounts()
        ret: Dict[str, Position] = {}
        for account in accounts:
            symbol = account['balance']['currency']
            spot_amount = float(account['balance']['amount']) + ret.get(symbol, 0)
            if spot_amount <= self.DUST_THRESHOLD:
                continue
            spot_amount_in_fiat = spot_amount / float(exchange_rates[symbol])
            ret[symbol] = Position(symbol, self.fiat, spot_amount, spot_amount_in_fiat, 0, 0)

        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)

    exchange = Coinbase()
    positions = exchange.get_positions()
    {print(json.dumps(position.to_dict(), indent=2)) for _, position in positions.items()}
