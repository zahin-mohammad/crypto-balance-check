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

    def publish_all_positions_by_exchange(self, positions_by_exchange: Dict[str, Dict[str, Position]]):
        mssgs: [str] = []
        total_fiat = 0
        max_len_mssg = 0
        for exchange, position_map in positions_by_exchange.items():
            mssgs.append(exchange.ljust(10))
            for position in position_map.values():
                total_fiat += position.total_fiat()
                message = "".ljust(5) + position.symbol.ljust(10) \
                          + " Spot ".ljust(10) + str(round(position.spot_amount, 5)).ljust(10) \
                          + " Margin ".ljust(10) + str(round(position.margin_amount, 5)).ljust(10) \
                          + " Fiat ".ljust(10) + str(round(position.total_fiat(), 2)).ljust(10)
                max_len_mssg = max(max_len_mssg, len(message))
                mssgs.append(message.ljust(100))
        total_fiat = "$" + "{:,}".format(round(total_fiat, 2)) + " CAD"
        mssgs.append("".ljust(55) + " Total ".ljust(10) + str(total_fiat).ljust(15))

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
