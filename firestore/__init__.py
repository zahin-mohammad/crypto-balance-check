import logging
import time
import firebase_admin
import os
import io
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

FIRESTORE_JSON = os.getenv('FIRESTORE_ADMIN')
if FIRESTORE_JSON is None:
    logger.warning("LOCAL USE")
else:
    with open("../firestore-admin.json", "w") as jsonFile:
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
        return [(int(t), balance) for t, balance in balance_json.items()]

    def update_historic_balances(self, positions_by_exchange, current_time: int = int(time.time())):
        total_fiat = 0
        for exchange, position_map in positions_by_exchange.items():
            for position in position_map.values():
                total_fiat += position.total_fiat()

        doc_ref = FIRESTORE_CLIENT.collection(BALANCE).document(self.__fiat)
        doc_ref.set({str(current_time): total_fiat}, merge=True)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import json

    load_dotenv(dotenv_path='../../.env')
    firestore = FireStore()

    balances = firestore.get_historic_balances('TEST')
    print(balances)
    # for i in range(20):
    #     firestore.update_historic_balances('TEST', 10 + i, i)
    balances = firestore.get_historic_balances('TEST')
    print(balances)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, figsize=(4, 4), dpi=300)
    plt.plot([balance[0] for balance in balances], [balance[1] for balance in balances])
    plt.title('title name')
    plt.xlabel('xAxis name')
    plt.ylabel('yAxis name')

    fig.canvas.draw()
    temp_canvas = fig.canvas
    plt.close()
    
    import PIL
    pil_image = PIL.Image.frombytes('RGB', temp_canvas.get_width_height(),  temp_canvas.tostring_rgb())
    print(pil_image)
    
    print(pil_image.size)

    in_mem_file = io.BytesIO()

    pil_image.save(in_mem_file, format='JPEG')
    print(in_mem_file.getvalue())
