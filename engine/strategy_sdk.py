from typing import Dict, Any
from abc import ABC, abstractmethod
from .types import StrategyVote
class Strategy(ABC):
    name: str
    def __init__(self, name:str): self.name=name
    @abstractmethod
    def on_price(self, price: float) -> StrategyVote: ...
