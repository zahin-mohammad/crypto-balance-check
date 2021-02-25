import json
import logging
import os
import traceback
from typing import Dict, Set
import requests

from exchanges.binance.auth import BinanceAuth
from exchanges.interface import Exchange, Position

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

GET = 'GET'
ACCOUNT = '/api/v3/account'
MARGIN_ACCOUNT = '/sapi/v1/margin/isolated/account'
TICKER = '/api/v3/ticker/24hr'
NAME = 'BINANCE'

BTCUSDT = 'BTCUSDT'
ETHUSDT = 'ETHUSDT'
USDT = 'USDT'
BTC = 'BTC'
ETH = 'ETH'


def get_fiat_map() -> Dict[str, str]:
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
    return {item['symbol']: item['id'] for item in data}


def get_usdt_to_fiat(fiat: str = 'CAD') -> float:
    fiat_map = get_fiat_map()
    r = requests.get(
        f'https://web-api.coinmarketcap.com/v1/tools/price-conversion?amount=1&convert_id=825&id={fiat_map[fiat]}')
    data = r.json()['data']
    return 1 / data['quote']['825']['price']


class Binance(Exchange):

    def __init__(self):
        super().__init__()
        self.binance_auth = BinanceAuth(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
        self.__valid = os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_API_SECRET')
        if self.__valid:
            logging.info(f"Initialized {self.name()} Exchange")
        else:
            logging.warning(f"{self.name()} Is Missing Configuration")

    def name(self) -> str:
        return NAME

    def __get_price_map(self) -> Set:
        price_response = self.binance_auth.send_public_request(TICKER)
        return {symbol_info['symbol'] for symbol_info in price_response}

    def __to_usdt(self, base: str, supported_pairs) -> float:
        if base == USDT:
            return 1
        elif (pair := base + USDT) in supported_pairs:
            return float(
                self.binance_auth.send_public_request(f'/api/v3/avgPrice?symbol={pair}')['price'])
        elif (pair := base + BTC) in supported_pairs:
            symbol_to_btc = float(
                self.binance_auth.send_public_request(f'/api/v3/avgPrice?symbol={pair}')['price'])
            btc_to_usdt = float(
                self.binance_auth.send_public_request(f'/api/v3/avgPrice?symbol={BTCUSDT}')['price'])
            return symbol_to_btc * btc_to_usdt
        elif (pair := base + ETH) in supported_pairs:
            symbol_to_eth = float(
                self.binance_auth.send_public_request(f'/api/v3/avgPrice?symbol={pair}')['price'])
            eth_to_usdt = float(
                self.binance_auth.send_public_request(f'/api/v3/avgPrice?symbol={ETHUSDT}')['price'])
            return symbol_to_eth * eth_to_usdt
        return 1

    def get_positions(self) -> Dict[str, Position]:
        if not self.__valid:
            return {}
        logging.info(f"{self.name()} get_positions")
        ret = {}
        try:
            spot_balances = self.binance_auth.send_signed_request(GET, ACCOUNT)['balances']
            margin_balances = self.binance_auth.send_signed_request(GET, MARGIN_ACCOUNT)['assets']
            price_map = self.__get_price_map()
            usdt_to_fiat = get_usdt_to_fiat(self.fiat)
        except Exception as e:
            traceback.print_exc()
            logging.error(e)
            return {}

        for balance in spot_balances:
            symbol = balance['asset']
            spot_amount = float(balance['free']) + float(balance['locked']) + ret.get(symbol, 0)
            if spot_amount <= self.DUST_THRESHOLD:
                continue
            spot_amount_in_fiat = spot_amount * self.__to_usdt(symbol, price_map) * usdt_to_fiat
            ret[symbol] = Position(symbol, self.fiat, spot_amount, spot_amount_in_fiat, 0, 0)

        for asset in margin_balances:
            symbol = asset['baseAsset']['asset']
            base_in_btc = float(asset['baseAsset']['netAssetOfBtc'])
            quote_in_btc = float(asset['quoteAsset']['netAssetOfBtc'])  # Usually negative
            total_in_btc = base_in_btc + quote_in_btc

            margin_amount = total_in_btc  # Default
            if margin_amount <= self.DUST_THRESHOLD:
                continue
            if symbol != BTC:
                base_to_btc = float(
                    self.binance_auth.send_public_request(f'/api/v3/avgPrice?symbol={symbol + BTC}')['price'])
                margin_amount = total_in_btc / base_to_btc
            margin_amount_in_fiat = margin_amount * self.__to_usdt(symbol, price_map) * usdt_to_fiat
            position = ret.get(symbol, Position(symbol, self.fiat))
            position.margin_amount = margin_amount
            position.margin_amount_in_fiat = margin_amount_in_fiat
            ret[symbol] = position
        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)

    exchange = Binance()
    positions = exchange.get_positions()
    {print(json.dumps(position.to_dict(), indent=2)) for _, position in positions.items()}
