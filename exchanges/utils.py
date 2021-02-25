from typing import Dict

import requests


def get_fiat_map() -> Dict[str, str]:
    r = requests.get('https://web-api.coinmarketcap.com/v1/fiat/map')
    data = r.json()['data']
    '''
    symbol -> {
        id
        name
        sign
        symbol
    }
    '''
    return {item['symbol']: item['id'] for item in data}


def get_usdt_to_fiat(fiat: str = 'CAD') -> float:
    fiat_map = get_fiat_map()
    r = requests.get(
        f'https://web-api.coinmarketcap.com/v1/tools/price-conversion?amount=1&convert_id=825&id={fiat_map[fiat]}')
    data = r.json()['data']
    return 1 / data['quote']['825']['price']