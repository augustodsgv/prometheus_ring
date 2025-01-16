from abc import ABC, abstractmethod
from src.ring.target import Target

class ServiceDiscovery(ABC):
    @abstractmethod
    def register_target(self, target: Target) -> None:
        pass

    @abstractmethod
    def deregister_target(self, target: Target) -> None:
        pass

    @abstractmethod
    def get_targets_json(self) -> list[Target]:
        pass