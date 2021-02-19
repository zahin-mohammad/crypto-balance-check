import json
import logging
from exchanges.interface import Exchange, positions, exchange_positions
from exchanges.binance import Binance
from exchanges.coinbase import Coinbase

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


class Exchanges:
    def __init__(self):
        self.__exchanges: [Exchange] = [
            Binance(),
            Coinbase()
        ]

    def get_total_fiat_value(self, currency: str = 'CAD') -> float:
        return sum([exchange.get_fiat_value(currency) for exchange in self.__exchanges])

    def get_all_positions(self) -> positions:
        ret = {}
        for exchange in self.__exchanges:
            current_positions = exchange.get_positions()
            for symbol, amount in current_positions.items():
                if symbol in ret:
                    ret[symbol] = ret[symbol] + amount
                else:
                    ret[symbol] = amount
        return ret

    def get_all_positions_by_exchange(self) -> exchange_positions:
        return {exchange.name(): exchange.get_positions() for exchange in self.__exchanges}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../.env')
    logger.setLevel(logging.DEBUG)

    exchanges = Exchanges()
    positions = exchanges.get_all_positions()
    print(json.dumps(positions, indent=2))
    positions_by_exchange = exchanges.get_all_positions_by_exchange()
    print(json.dumps(positions_by_exchange, indent=2))
    total_fiat_value = exchanges.get_total_fiat_value()
    print(total_fiat_value)
