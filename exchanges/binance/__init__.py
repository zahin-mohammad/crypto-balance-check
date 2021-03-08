import json
import logging
import os
import traceback
from typing import Dict, Set

from exchanges.binance.auth import BinanceAuth
from exchanges.interface import Exchange, Position
from exchanges.utils import get_usdt_to_fiat

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
            base_symbol = asset['baseAsset']['asset']
            quote_symbol = asset['quoteAsset']['asset']
            base_amount = float(asset['baseAsset']['netAsset'])
            quote_amount = float(asset['quoteAsset']['netAsset'])
            # Amounts can be negative
            if abs(base_amount) <= self.DUST_THRESHOLD and abs(quote_amount) <= self.DUST_THRESHOLD:
                continue

            base_in_fiat = base_amount * self.__to_usdt(base_symbol, price_map) * usdt_to_fiat
            position = ret.get(base_symbol, Position(base_symbol, self.fiat))
            position.margin_amount += base_amount
            position.margin_amount_in_fiat += base_in_fiat
            ret[base_symbol] = position

            quote_in_fiat = quote_amount * self.__to_usdt(quote_symbol, price_map) * usdt_to_fiat
            print(quote_in_fiat)
            position = ret.get(quote_symbol, Position(quote_symbol, self.fiat))
            position.margin_amount += quote_amount
            position.margin_amount_in_fiat += quote_in_fiat
            ret[quote_symbol] = position
        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)

    exchange = Binance()
    positions = exchange.get_positions()
    {print(json.dumps(position.to_dict(), indent=2)) for _, position in positions.items()}
