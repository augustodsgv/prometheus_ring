from typing import Any
from abc import ABC, abstractmethod

class Node(ABC):
    @abstractmethod
    def insert(self, key: str, value: Any) -> None:
        ...
    
    @abstractmethod
    def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    def list_items(self)->list[Any]:
        ...

    @abstractmethod
    def is_full(self) -> bool:
        ...

    @abstractmethod
    def delete(self, key: str) -> Any:
        ...

    @abstractmethod
    def update(self, key: str, new_value: Any) -> None:
        ...

    @abstractmethod
    def has_key(self, key: str) -> bool:
        ...

    @abstractmethod
    def clean_keys(self)->None:
        ...

    @abstractmethod
    def export_keys(self, other_node: 'Node', first_key_hash: int)->None:
        ...

    @abstractmethod
    def calc_mid_hash(self)->int:
        ...
    
    @property
    @abstractmethod
    def load(self) -> float:
        ...

    