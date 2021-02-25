import json
import logging
from typing import Dict

from exchanges.interface import Exchange, Position
from exchanges.binance import Binance
from exchanges.coinbase import Coinbase
from exchanges.kucoin import KuCoin
from exchanges.newton import Newton

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


class Exchanges:
    def __init__(self):
        self.__exchanges: [Exchange] = [
            Binance(),
            Coinbase(),
            Newton(),
            KuCoin()
        ]

    def get_all_positions(self) -> [Position]:
        ret = {}
        for exchange in self.__exchanges:
            for p in exchange.get_positions().values():
                position = ret.get(p.symbol, Position(p.symbol, exchange.fiat))
                position.spot_amount += p.spot_amount
                position.spot_amount_in_fiat += p.spot_amount_in_fiat
                position.margin_amount += p.margin_amount
                position.margin_amount_in_fiat += p.margin_amount_in_fiat
                ret[position.symbol] = position
        return ret.values()

    def get_all_positions_by_exchange(self) -> Dict[str, Dict[str, Position]]:
        return {exchange.name(): exchange.get_positions() for exchange in self.__exchanges}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../.env')
    logger.setLevel(logging.DEBUG)

    exchanges = Exchanges()
    # positions = exchanges.get_all_positions()
    # _ = {print(json.dumps(position.to_dict(), indent=2)) for position in positions}
    positions_by_exchange = exchanges.get_all_positions_by_exchange()
    # _ = {print(json.dumps(dict(position.to_dict().items() | [("Exchange", exchange)]), indent=2)) for exchange, position_map in positions_by_exchange.items() for position in position_map.values()}

    mssgs: [str] = []
    total_fiat = 0
    max_len_mssg = 0
    for exchange, position_map in positions_by_exchange.items():
        mssgs.append(exchange.ljust(10))
        for position in position_map.values():
            total_fiat += position.total_fiat()
            message = "".ljust(5) + position.symbol.ljust(10) \
                      + " Spot ".ljust(10) + str(position.spot_amount).ljust(16) \
                      + " Margin ".ljust(10) + str(position.margin_amount).ljust(16) \
                      + " Fiat ".ljust(10) + str(position.total_fiat()).ljust(16)
            max_len_mssg = max(max_len_mssg, len(message))
            mssgs.append(message)
    total_fiat = "$" + "{:,}".format(round(total_fiat, 2)) + " CAD"
    mssgs.append("".ljust(67) + " Total ".ljust(10) + str(total_fiat).ljust(16))
    for m in mssgs:
        print(m)
    print("\n".join(mssgs))

