from abc import ABC, abstractmethod
from typing import Any

class AbstractDataType(ABC):
    @abstractmethod
    def insert(self, key: int, value: Any)->None:
        ...
    
    @abstractmethod
    def search(self, key)->Any | None:
        ...

    # @abstractmethod
    # def has_key(self, key: int)->bool:
    #     ...

    @abstractmethod
    def update(self, key: int, new_value: Any)->Any | None:
        ...

    @abstractmethod
    def remove(self, key: int)->Any | None:
        ...

    @abstractmethod
    def list(self)->list[Any]:
        ...

    @abstractmethod
    def find_max_smaller_than(self, key: int)->Any:
        ...

    # @abstractmethod
    # def find_min_greater_than(self, key: int)->Any:
    #     ...