import hashlib
import hmac
import json
import logging
import os
import time
from urllib.parse import urlencode
import requests
from ratelimit import limits
from exchanges.interface import Exchange, positions

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

NAME = 'BINANCE'
BASE_URL = 'https://api.binance.com'
ONE_MINUTE = 60

BTCUSDT = 'BTCUSDT'
ETHUSDT = 'ETHUSDT'


def get_timestamp():
    return int(time.time() * 1000)


def get_fiat_map():
    r = requests.get('https://web-api.coinmarketcap.com/v1/fiat/map')
    data = r.json()['data']
    '''
    symbol -> {
        id
        name
        sign
        symbol
    }
    '''
    return {item['symbol']: item for item in data}


# TODO: Remove Hardcoded Strings
def get_usdt_to_fiat(fiat_currency_id: int = 2784):
    r = requests.get(
        f'https://web-api.coinmarketcap.com/v1/tools/price-conversion?amount=1&convert_id=825&id={fiat_currency_id}')
    data = r.json()['data']
    return 1 / data['quote']['825']['price']


class Binance(Exchange):

    def __init__(self):
        self.__API_KEY = os.getenv('BINANCE_API_KEY')
        self.__API_SECRET = os.getenv('BINANCE_API_SECRET')
        logging.info(f"Initialized {self.name()} Exchange")

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

    # used for sending request requires the signature
    @limits(calls=10, period=ONE_MINUTE)
    def __send_signed_request(self, http_method, url_path, payload=None):
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
    @limits(calls=10, period=ONE_MINUTE)
    def __send_public_request(self, url_path, payload=None):
        if payload is None:
            payload = {}
        query_string = urlencode(payload, True)
        url = BASE_URL + url_path
        if query_string:
            url = url + '?' + query_string
        print("{}".format(url))
        response = self.__dispatch_request('GET')(url=url)
        return response.json()

    def name(self) -> str:
        return NAME

    def get_fiat_value(self, currency: str = 'CAD') -> float:
        logging.info(f"{self.name()} get_fiat_value")

        fiat_map = get_fiat_map()
        if currency not in fiat_map:
            logging.error(f'Invalid currency {currency}')
            exit()
        usdt_to_fiat = get_usdt_to_fiat(fiat_map[currency]['id'])
        total_usdt = 0

        try:
            positions = self.get_positions()
            price_response = self.__send_public_request('/api/v3/ticker/24hr')
            price_set = {symbol_info['symbol']for symbol_info in price_response}
            usdt_val = 0

            for symbol, amount in positions.items():
                if symbol == 'USDT':
                    usdt_val = amount
                elif symbol + 'USDT' in price_set:
                    pair = symbol + 'USDT'
                    average_price_symbol_usdt = float(self.__send_public_request(f'/api/v3/avgPrice?symbol={pair}')['price'])
                    usdt_val = amount * average_price_symbol_usdt
                # For weird symbols like BETH
                # Check BETHBTC
                # Check BETHETH
                else:
                    btc_pair = symbol + 'BTC'
                    eth_pair = symbol + 'ETH'
                    if btc_pair in price_set:
                        average_price_btc_pair = float(
                            self.__send_public_request(f'/api/v3/avgPrice?symbol={btc_pair}')['price'])
                        average_price_btc_usdt = float(
                            self.__send_public_request(f'/api/v3/avgPrice?symbol={BTCUSDT}')['price'])
                        usdt_val = amount * average_price_btc_pair * average_price_btc_usdt
                    elif eth_pair in price_set:
                        average_price_eth_pair = float(
                            self.__send_public_request(f'/api/v3/avgPrice?symbol={eth_pair}')['price'])
                        average_price_eth_usdt = float(
                            self.__send_public_request(f'/api/v3/avgPrice?symbol={ETHUSDT}')['price'])
                        usdt_val = amount * average_price_eth_pair * average_price_eth_usdt

                # print(f'{symbol}: {amount} -> {currency}: {usdt_val * usdt_to_fiat}')
                total_usdt += usdt_val
        except Exception as e:
            logging.error(e)
        return total_usdt * usdt_to_fiat

    def get_positions(self) -> positions:
        logging.info(f"{self.name()} get_positions")
        ret = {}
        try:
            response = self.__send_signed_request('GET', '/api/v3/account')
            price_response = self.__send_public_request('/api/v3/ticker/24hr')
            price_map = {symbol_info['symbol']: float(symbol_info['prevClosePrice']) for symbol_info in
                         price_response}

            balances = response["balances"]
            for balance in balances:
                balance_total = float(balance['free']) + float(balance['locked'])
                if balance_total <= 0.0000001:
                    continue
                ret[balance['asset']] = balance_total

            response = self.__send_signed_request('GET', '/sapi/v1/margin/isolated/account')
            for asset in response['assets']:
                base = asset['baseAsset']['asset']
                base_in_btc = float(asset['baseAsset']['netAssetOfBtc'])
                quote_in_btc = float(asset['quoteAsset']['netAssetOfBtc'])  # Usually negative

                total_in_btc = base_in_btc + quote_in_btc

                base_total = total_in_btc
                if base != 'BTC':
                    base_to_btc_price = price_map[base + "BTC"]
                    base_total = total_in_btc / base_to_btc_price
                if base_total <= 0.00001:
                    continue

                if base in ret:
                    ret[base] = ret[base] + base_total
                else:
                    ret[base] = base_total
        except Exception as e:
            logging.error(e)
        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)
    # print(get_usdt_to_fiat())
    exchange = Binance()
    positions = exchange.get_positions()
    print(json.dumps(positions, indent=2))
    fiat_value = exchange.get_fiat_value()
    print(fiat_value)
