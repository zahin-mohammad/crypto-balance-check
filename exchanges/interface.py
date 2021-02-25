import json
from typing import Dict, Any


# Symbol -> spot_amount, spot_amount_in_fiat, margin_amount, margin_amount_in_fiat
class Position():
    def to_dict(self) -> {}:
        return {
            "Symbol": self.symbol,
            "Fiat": self.fiat,
            "Spot Amount": self.spot_amount,
            "Spot Amount in Fiat": self.spot_amount_in_fiat,
            "Margin Amount": self.margin_amount,
            "Margin Amount in Fiat": self.margin_amount_in_fiat
        }
    def total_fiat(self) -> float:
        return self.margin_amount_in_fiat + self.spot_amount_in_fiat

    def __init__(self, symbol: str, fiat: str, spot_amount: float = 0, spot_amount_in_fiat: float = 0, margin_amount: float = 0,
                 margin_amount_in_fiat: float = 0):
        super().__init__()
        self.symbol: str = symbol
        self.fiat: str = fiat
        self.spot_amount = spot_amount
        self.spot_amount_in_fiat = spot_amount_in_fiat
        self.margin_amount = margin_amount
        self.margin_amount_in_fiat = margin_amount_in_fiat


class Exchange:
    def __init__(self, fiat_currency: str = 'CAD'):
        self.fiat = fiat_currency
        self.DUST_THRESHOLD = 0.0000001

    def name(self) -> str:
        raise Exception('Interface Method')

    #
    # def get_fiat_value(self, currency: str) -> float:
    #     raise Exception('Interface Method')

    def get_positions(self) -> Dict[str, Position]:
        raise Exception('Interface Method')
