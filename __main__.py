import logging
from exchanges import Exchanges
from imgur import Imgur
from slack import Slack
from firestore import FireStore
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Starting crypto-balance-check worker')

    exchanges = Exchanges()
    slack = Slack()
    firestore = FireStore()
    imgur = Imgur()

    positions_by_exchange = exchanges.get_all_positions_by_exchange()
    slack.publish_all_positions_by_exchange(positions_by_exchange)
    firestore.update_historic_balances(positions_by_exchange)
    balances = firestore.get_historic_balances()
    url = imgur.send_graph([b[0] for b in balances], [b[1] for b in balances])
    slack.publish_url(url)

    logger.info('Exiting crypto-balance-check worker')
