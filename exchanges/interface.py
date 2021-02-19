from typing import Dict

positions = Dict[str, float]
exchange_positions = Dict[str, positions]


class Exchange:
    def name(self) -> str:
        raise Exception('Interface Method')

    def get_fiat_value(self, currency: str) -> float:
        raise Exception('Interface Method')

    def get_positions(self) -> positions:
        raise Exception('Interface Method')
