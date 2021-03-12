import logging
import time
from datetime import date
import firebase_admin
import os
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

FIRESTORE_JSON = os.getenv('FIRESTORE_ADMIN')
if FIRESTORE_JSON is None:
    logger.warning("LOCAL USE")
else:
    with open("firestore-admin.json", "w") as jsonFile:
        jsonFile.write(FIRESTORE_JSON)

cred = credentials.Certificate('firestore-admin.json')
firebase_admin.initialize_app(cred)
FIRESTORE_CLIENT = firestore.client()

HISTORY = 'HISTORY'
BALANCE = 'BALANCE'


class FireStore:
    def __init__(self):
        self.__fiat = os.getenv('FIAT_CURRENCY')

    def get_historic_balances(self):
        doc_ref = FIRESTORE_CLIENT.collection(BALANCE).document(self.__fiat)
        balance_json = doc_ref.get().to_dict()
        if balance_json is None:
            return []
        balances = [(int(t), balance) for t, balance in balance_json.items()]
        balances.sort(key=lambda x: x[0])
        return balances

    def update_historic_balances(self, positions_by_exchange, current_time: int = int(time.time())):
        total_fiat = 0
        for exchange, position_map in positions_by_exchange.items():
            for position in position_map.values():
                total_fiat += position.total_fiat()

        doc_ref = FIRESTORE_CLIENT.collection(BALANCE).document(self.__fiat)
        doc_ref.set({str(current_time): total_fiat}, merge=True)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import matplotlib.pyplot as plt
    load_dotenv(dotenv_path='../.env')

    firestore = FireStore()
    balances = firestore.get_historic_balances()

    plt.style.use('ggplot')
    fig, ax = plt.subplots(1, dpi=300)
    x, y = [i for i in range(len(balances))], [balance[1] for balance in balances]

    ax.plot(x, y, alpha=0.5)
    ax.axes.xaxis.set_visible(False)
    ax.yaxis.set_major_formatter('${x:1.2f}')
    ax.yaxis.set_tick_params(which='major',labelleft=False, labelright=True)
    start = date.fromtimestamp(balances[0][0])
    end = date.fromtimestamp(balances[-1][0])
    plt.title(f'Crypto Balance: {start} - {end}')
    plt.xlabel('Time')
    plt.ylabel('CAD $')
    plt.close()
    fig.show()
