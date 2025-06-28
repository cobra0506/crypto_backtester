from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, symbol: str, interval: str, data: pd.DataFrame, config: dict):
        self.symbol = symbol
        self.interval = interval
        self.data = data
        self.config = config
        self.trades = []

    @abstractmethod
    def run(self):
        """
        Execute the strategy logic on self.data and populate self.trades
        """
        pass

    def get_results(self):
        return self.trades
