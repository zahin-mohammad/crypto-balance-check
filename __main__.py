import logging
from exchanges import Exchanges
from slack import Slack
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Starting crypto-balance-check worker')

    exchanges = Exchanges()
    slack = Slack()

    positions = exchanges.get_all_positions()
    slack.publish_all_positions(positions)

    positions_by_exchange = exchanges.get_all_positions_by_exchange()
    slack.publish_all_positions_by_exchange(positions_by_exchange)

    total_fiat_value = exchanges.get_total_fiat_value()
    slack.publish_total_fiat_value(total_fiat_value)

    logger.info('Exiting crypto-balance-check worker')
