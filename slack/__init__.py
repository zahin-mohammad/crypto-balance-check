import json
import logging
import os
import sys
import requests
from exchanges import positions, exchange_positions

logger = logging.getLogger(__name__)


class Slack:
    def __init__(self):
        self.__webhook = os.getenv('SLACK_WEBHOOK')
        if self.__webhook is None:
            logger.error('FORGOT SLACK WEBHOOK')
            sys.exit()

    def publish_total_fiat_value(self, total_fiat_value: float, currency: str = 'CAD'):
        total_fiat_value = "{:,}".format(total_fiat_value)
        message_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hi Zahin, the total `{currency}` value of your positions is $`{total_fiat_value}`!\n"
            }
        }]
        requests.post(self.__webhook, data=json.dumps({"blocks": message_blocks}), headers={
            'Content-Type': 'application/json'}, verify=True)

    def publish_all_positions(self, all_positions: positions):
        message_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hi Zahin, here are your positions!\n"
            }
        }]
        position_info = ''
        for symbol, amount in all_positions.items():
            amount = "{:,}".format(amount)
            position_info += f"`{symbol}`:\t{amount}\n"

        message_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{position_info}"
            }
        })

        requests.post(self.__webhook, data=json.dumps({"blocks": message_blocks}), headers={
            'Content-Type': 'application/json'}, verify=True)

    def publish_all_positions_by_exchange(self, all_positions_by_exchange: exchange_positions):
        message_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hi Zahin, here are your positions by exchange!\n"
            }
        }]
        for exchange, all_positions in all_positions_by_exchange.items():
            position_info = ''
            for symbol, amount in all_positions.items():
                amount = "{:,}".format(amount)
                position_info += f"\t`{symbol}`:\t{amount}\n"
            exchange_position_info = f'{exchange}:\n{position_info}'
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{exchange_position_info}"
                }
            })
        requests.post(self.__webhook, data=json.dumps({"blocks": message_blocks}), headers={
            'Content-Type': 'application/json'}, verify=True)
