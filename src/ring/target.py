from pydantic import BaseModel, Field
from src.hash import hash

class Target(BaseModel, frozen=True):
    id: str
    name: str
    address: str
    metrics_port: int = Field(default=8000)
    metrcs_path: str = Field(default='/metrics')

    @property
    def endpoint(self)->str:
        return f'{self.address}:{self.metrics_port}'

