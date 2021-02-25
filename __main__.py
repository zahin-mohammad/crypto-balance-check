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

    positions_by_exchange = exchanges.get_all_positions_by_exchange()
    slack.publish_all_positions_by_exchange(positions_by_exchange)

    logger.info('Exiting crypto-balance-check worker')
