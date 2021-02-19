import json, hmac, hashlib, time, requests
import os
from ratelimit import limits
from requests import Response
from requests.auth import AuthBase
from requests.utils import to_native_string
import logging
from exchanges.interface import Exchange, positions

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

NAME = 'COINBASE'
BASE_URL = 'https://api.coinbase.com'
LIST_ACCOUNTS = '/v2/accounts'
EXCHANGE_RATES = '/v2/exchange-rates?currency='
SIXTY_MINUTES = 3600


# Create custom authentication for Coinbase API
class CoinbaseWalletAuth(AuthBase):
    def __init__(self, api_key, secret_key, api_version: str = "2021-02-18"):
        self.__api_key = api_key
        self.__api_secret_key = secret_key
        self.__api_version = api_version
        logging.info("Initialized Coinbase Wallet Auth")

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


class Coinbase(Exchange):
    def __init__(self):
        self.__auth = CoinbaseWalletAuth(
            api_key=os.getenv('COINBASE_API_KEY'),
            secret_key=os.getenv('COINBASE_API_SECRET'))
        logging.info(f"Initialized {self.name()} Exchange")

    def name(self) -> str:
        return NAME

    @limits(calls=10000, period=SIXTY_MINUTES)
    def call_api(self, method: str, url: str) -> Response:
        return requests.request(method=method, url=url, auth=self.__auth)

    def get_fiat_value(self, currency: str = 'CAD') -> float:
        logging.info(f"{self.name()} get_fiat_value")
        total_fiat_value = 0
        try:
            r = self.call_api('GET', BASE_URL + EXCHANGE_RATES + currency)
            # print(json.dumps(r.json(), indent=2))
            exchange_rates = r.json()['data']['rates']
            total_fiat_value = 0
            for (symbol, amount) in self.get_positions().items():
                exchange_rate = float(exchange_rates[symbol])
                value = amount / exchange_rate
                logging.debug(f"{symbol} {value}")
                total_fiat_value += value
        except Exception as e:
            logging.error(e)
        return total_fiat_value

    def get_positions(self) -> positions:
        logging.info(f"{self.name()} get_positions")
        next_uri = LIST_ACCOUNTS
        ret = {}
        try:
            while next_uri is not None:
                r = self.call_api('GET', BASE_URL + next_uri)
                pagination = r.json()['pagination']
                next_uri = pagination['next_uri']
                data = r.json()['data']
                for account in data:
                    symbol = account['balance']['currency']
                    amount = float(account['balance']['amount'])
                    if amount <= 0.0000001:
                        continue
                    if symbol in ret:
                        ret[symbol] = ret[symbol] + amount
                    else:
                        ret[symbol] = amount
        except Exception as e:
            logging.error(e)
        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)

    exchange = Coinbase()
    positions = exchange.get_positions()
    print(json.dumps(positions, indent=2))
    fiat_value = exchange.get_fiat_value()
    print(fiat_value)
