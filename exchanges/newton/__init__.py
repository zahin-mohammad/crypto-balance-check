import hmac
import json
import logging
import os
import traceback
from base64 import b64encode
from datetime import datetime
from hashlib import sha256
from math import floor
from typing import Dict
import requests

from exchanges import Exchange, Position
from exchanges.utils import get_usdt_to_fiat

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

ENCODING = "utf-8"
BASE_URL = "https://api.newton.co"
BINANCE_BASE_URL = 'https://api.binance.com'
BALANCES = "/v1/balances"


class Newton(Exchange):

    def __init__(self):
        super().__init__()
        self.__client_id = os.getenv('NEWTON_CLIENT_ID')
        self.__client_secret = os.getenv('NEWTON_API_SECRET')
        self.__valid = self.__client_secret and self.__client_id and os.getenv('FIAT_CURRENCY') == 'CAD'
        if self.__valid:
            logging.info(f"Initialized {self.name()} Exchange")
        else:
            logging.warning(f"{self.name()} Is Missing Configuration")

    def __get_header(self, path) -> Dict[str, str]:
        current_time = str(floor(datetime.now().timestamp()))
        # If the request has a body, you would use this instead of empty string below (replace BODY with actual request body):
        # hashed_body = sha256(BODY).hexdigest()
        signature_parameters = [
            "GET",
            "",
            path,
            "",  # If the request has a body, this would be hashed_body
            current_time
        ]
        signature_data = ":".join(signature_parameters).encode(ENCODING)

        computed_signature = hmac.new(
            self.__client_secret.encode(ENCODING),
            msg=signature_data,
            digestmod=sha256
        ).digest()

        NewtonAPIAuth = self.__client_id + ":" + b64encode(computed_signature).decode()
        NewtonDate = current_time
        return {
            "NewtonAPIAuth": NewtonAPIAuth,
            "NewtonDate": NewtonDate
        }

    def name(self) -> str:
        return "NEWTON"

    # HACK because Newton doesnt have a price endpoint
    def __to_usdt(self, symbol) -> float:
        return float(requests.get(f'{BINANCE_BASE_URL}/api/v3/avgPrice?symbol={symbol + "USDT"}').json()['price'])

    def get_positions(self) -> Dict[str, Position]:
        if not self.__valid:
            return {}
        try:
            data = requests.get(f"{BASE_URL}{BALANCES}", headers=self.__get_header(BALANCES)).json()
        except Exception as e:
            traceback.print_exc()
            logging.error(e)
            return {}
        ret = {}
        for symbol, amount in data.items():
            if symbol == 'CAD' or amount <= self.DUST_THRESHOLD:
                continue
            spot_amount = amount
            spot_amount_in_fiat = spot_amount * self.__to_usdt(symbol) * get_usdt_to_fiat(self.fiat)
            ret[symbol] = Position(symbol, self.fiat, spot_amount, spot_amount_in_fiat, 0, 0)
        return ret


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env')
    logger.setLevel(logging.DEBUG)

    exchange = Newton()
    positions = exchange.get_positions()
    {print(json.dumps(position.to_dict(), indent=2)) for _, position in positions.items()}
