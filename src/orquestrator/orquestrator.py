from abc import ABC, abstractmethod

class Orquestrator(ABC):
    @abstractmethod
    def create_instance(self)->None:
        ...

    @abstractmethod
    def delete_instance(self)->None:
        ...

    @abstractmethod
    def check_instance_health(self)->None:
        ...
        