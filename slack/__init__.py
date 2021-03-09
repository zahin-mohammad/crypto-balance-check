import json
import logging
import os
import sys
from typing import Dict

import requests
from exchanges import Position

logger = logging.getLogger(__name__)


class Slack:
    def __init__(self):
        self.__webhook = os.getenv('SLACK_WEBHOOK')
        if self.__webhook is None:
            logger.error('FORGOT SLACK WEBHOOK')
            sys.exit()

    def publish_url(self, link:str):
        message_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Balance Graph\n{link}"
            }
        }]
        r = requests.post(self.__webhook,
                          data=json.dumps({"text": "Your Crypto Balance Graph", "blocks": message_blocks}),
                          headers={'Content-Type': 'application/json'}, verify=True)

    def publish_all_positions_by_exchange(self, positions_by_exchange: Dict[str, Dict[str, Position]]):
        mssgs: [str] = []
        total_fiat = 0
        max_len_mssg = 0
        LEVEL = 2
        currency = ""
        for exchange, position_map in positions_by_exchange.items():
            mssgs.append(exchange.ljust(10))
            for position in position_map.values():
                if not currency:
                    currency = position.fiat
                total_fiat += position.total_fiat()
                message = "".ljust(LEVEL) + position.symbol.ljust(5) \
                          + "".ljust(17) \
                          + " Fiat ".ljust(10) + str(round(position.total_fiat(), 2)).ljust(9)
                mssgs.append(message)
                message = "".ljust(LEVEL*2)  \
                          + " Spot ".ljust(10) + str(round(position.spot_amount, 5)).ljust(9)
                mssgs.append(message)
                message = "".ljust(LEVEL*2)  \
                          + " Margin ".ljust(10) + str(round(position.margin_amount, 5)).ljust(9)
                mssgs.append(message)
                message = "".ljust(LEVEL * 2) \
                          + " Total ".ljust(10) + str(round(position.total_base(), 5)).ljust(9)
                max_len_mssg = max(max_len_mssg, len(message))
                mssgs.append(message)
            mssgs.append("-"*(LEVEL+5+17+10+16))
        total_fiat = "$" + "{:,}".format(round(total_fiat, 2)) + f" {currency}"
        mssgs.append("".ljust(LEVEL + 5 + 17) + " Total ".ljust(10) + str(total_fiat).ljust(16))

        for m in mssgs:
            print(m)
        message_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```" + "\n".join(mssgs) + "```"
            }
        }]
        r = requests.post(self.__webhook,
                          data=json.dumps({"text": "Your Crypto Summary", "blocks": message_blocks}),
                          headers={'Content-Type': 'application/json'}, verify=True)
        print(r.status_code)
        print(r.text)
