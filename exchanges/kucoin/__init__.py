import json
import logging
import os
from typing import Dict

from kucoin.client import User, Market

from exchanges import Exchange, Position

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

TRADE = 'trade'
MAIN = 'main'
MARGIN = 'margin'

class KuCoin(Exchange):

    def __init__(self):
        super().__init__()
        self.__api_key = os.getenv('KUCOIN_API_KEY')
        self.__api_secret = os.getenv('KUCOIN_API_SECRET')
        self.__api_passphrase = os.getenv('KUCOIN_API_PASSPHRASE')
        self.__valid = self.__api_key and self.__api_secret and self.__api_passphrase
        if self.__valid:
            logging.info(f"Initialized {self.name()} Exchange")
            self.__user = User(self.__api_key, self.__api_secret, self.__api_passphrase)
            self.__market = Market()
        else:
            logging.warning(f"{self.name()} Is Missing Configuration")

    def name(self) -> str:
        return "KUCOIN"

    def get_positions(self) -> Dict[str, Position]:
        if not self.__valid:
            return {}
        ret = {}
        accounts = self.__user.get_account_list()
        prices = self.__market.get_fiat_price(base=self.fiat)
        for account in accounts:
            symbol = account['currency']
            account_type = account['type']
            account_balance = float(account['balance'])
            symbol_to_fiat = float(prices[symbol])
            if account_balance <= self.DUST_THRESHOLD:
                continue
            position = ret.get(symbol, Position(symbol, self.fiat))
            if account_type == TRADE or account_type == MAIN:
                position.spot_amount += account_balance
            elif account_type == MARGIN:
                position.margin_amount += account_balance
            position.spot_amount_in_fiat = position.spot_amount * symbol_to_fiat
            position.margin_amount_in_fiat = position.margin_amount * symbol_to_fiat
            ret[symbol] = position
        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)

    exchange = KuCoin()
    positions = exchange.get_positions()
    {print(json.dumps(position.to_dict(), indent=2)) for _, position in positions.items()}



