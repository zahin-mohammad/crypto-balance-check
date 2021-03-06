import logging
import os
import matplotlib.pyplot as plt
from datetime import date
from imgurpython import ImgurClient

plt.style.use('ggplot')
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

temp_file_name = 'temp.png'
CRYPTO_BALANCE_CHECK = 'Crypto Balance Check'


class Imgur:
    def __init__(self):
        client_id = os.getenv('IMGUR_CLIENT_ID')
        client_secret = os.getenv('IMGUR_CLIENT_SECRET')
        self.__fiat = os.getenv('FIAT_CURRENCY')
        if client_id == "" or client_secret == "":
            logger.warning('INVALID IMGUR CREDENTIALS')
        else:
            logger.warning('IMGUR INITIALIZED')
            self.client = ImgurClient(client_id, client_secret)

    def _create_graph(self, x, y):
        if len(x) == 0 or len(y) == 0:
            return ""
        start, end = date.fromtimestamp(x[0]), date.fromtimestamp(x[-1])
        fig, ax = plt.subplots(1, dpi=300)
        ax.plot(x, y, alpha=0.5)
        ax.axes.xaxis.set_visible(False)
        ax.yaxis.set_major_formatter('${x:1.2f}')
        ax.yaxis.set_tick_params(which='major', labelleft=False, labelright=True)
        plt.title(f'Crypto Balance: {start} - {end}')
        plt.xlabel('Time')
        plt.ylabel(f'{self.__fiat} $')
        fig.savefig(temp_file_name)
        plt.close()
        return temp_file_name

    def send_graph(self, x, y, title=CRYPTO_BALANCE_CHECK, xlabel='Time', ylabel: str = '') -> str:
        if self.client is None:
            logger.warning('INVALID IMGUR CREDENTIALS')
            return ""
        if ylabel == '':
            ylabel = f'{self.__fiat} $'
        config = {
            'title': title,
            'description': f'{x[0]} to {x[-1]}'
        }
        filename = self._create_graph(x, y)
        logger.warning('UPLOADING IMAGE')
        return self.client.upload_from_path(filename, config)['link']


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(dotenv_path='../.env')
    import numpy as np

    x = np.linspace(-np.pi, np.pi, 201)
    y = np.sin(x)

    imgur = Imgur()
    response = imgur.send_graph(x, y)
    print(response)
