from pydantic import BaseModel, Field

class Target(BaseModel, frozen=True):
    id: str
    name: str
    address: str
    metrics_port: int = Field(default=8000)
    metrics_path: str = Field(default='/metrics')

    @property
    def endpoint(self)->str:
        return f'{self.address}:{self.metrics_port}'

    # @property
    # def hash(self)->int:
    #     return hash(id)         # For now, only using the id to hash