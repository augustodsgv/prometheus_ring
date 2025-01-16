from typing import Any
from .node import Node
from abc import ABC, abstractmethod

class Ring(ABC):
    @abstractmethod
    def insert(self, value, key: str | None = None)->None | Node:
        pass

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def update(self, key: str, new_value: Any) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None | Node:
        pass
    