from .target import Target
from .hash import stable_hash
import yaml

class Node:
    """
    Represents a node in the prometheus ring, i.e. a prometheus instance
    """
    def __init__(
            self, index: int,
            capacity: int,
            sd_url: str | None = None,
            sd_port: str | None = None,
            scrape_interval = '1m',
            refresh_interval = '1m',
            port: int | None = None,
            replica_count: int = 1,
            metrics_database_url: str | None = None,
            metrics_database_port: int | None = None,
            metrics_database_path: str | None = None,
        ) -> None:

        self.index = index
        self.capacity = capacity
        self.replica_count = replica_count
        self.ready = False
        self.targets = dict()
        self.keys_to_delete = list()
        self.scrape_interval = scrape_interval
        self.refresh_interval = refresh_interval
        self.sd_url = sd_url
        self.sd_port = sd_port
        self.port = port
        self.metrics_database_url = metrics_database_url
        self.metrics_database_port = metrics_database_port
        self.metrics_database_path = metrics_database_path

    def insert(self, key: str, target: Target) -> None:
        """
        Inserts a node
        """
        self.targets[key] = target

    def has_key(self, key: str) -> bool:
        """
        Returns True if the key is in the node
        """
        return key in self.targets
    
    def get(self, key: str) -> Target | None:
        """
        Searchs and returns the node.
        Returns None if not found
        """
        if not self.has_key(key):
            return None
        return self.targets[key]
    
    def is_full(self) -> bool:
        """
        Returns whether the node is full or not
        """
        return len(self.targets) >= self.capacity
    
    def list_items(self)->list[Target]:
        """
        Lists all targets from this node
        """
        return list(self.targets.values())

    def delete(self, key: str) -> Target:
        """
        Deletes a target from the node.
        """
        if not self.has_key(key):
            # raise KeyNotFoundError(f'Key {key} not found')
            raise Exception(f'Key {key} not found')
        return self.targets.pop(key)
    
    def update(self, key: str, new_target: Target) -> None:
        """
        Updates the target of a key. Returns old object if update or None if didn't find
        This is problably not useful in this implementation
        """
        self.targets[key] = new_target
    
    def export_keys(self, other_node: 'Node', first_key_hash: int = -1)->None:
        """
        Exports all instances with hash equal or greater than first_key_hash to another node
        If no fist_key_hash is provided, exports all keys to the other node
        """
        for key, target in self.targets.items():
            if stable_hash(key) >= first_key_hash:
                other_node.insert(key, target)     # Import and delete the key from the other node
                self.keys_to_delete.append(key)
        self.clean_keys()

    def clean_keys(self)->None:
        """
        Removes keys sent to other node
        """
        for key in self.keys_to_delete:
            self.delete(key)
        self.keys_to_delete = list()

    def calc_mid_hash(self)->int:
        """
        Calculates the mean hash of all of the node
        A Future discussion if this is the best way to calculate the median instead.
        """
        return sum([stable_hash(key) for key in self.targets.keys()]) // len(self.targets.keys())
    
    # def __str__(self) -> str:
    #     base_str = []
    #     for key, target in self.targets.items():
    #         base_str.append(f'{key}: {target}')

    #     return ' '.join(base_str)

    @property
    def load(self) -> int:
        """
        Calculates the load of the node. Value ranges from 0 to 100
        """
        return int(len(self.targets.keys()) / self.capacity * 100)
    
    # Prometheus specific functions
    def set_node_ready(self) -> None:
        """
        Define the node as ready.
        This is either because the node is initializating or dead
        """
        self.ready = True

    def set_node_not_ready(self) -> None:
        """
        Define the node as not ready
        """
        self.ready = False  

    @property
    def yaml(self)->str:
        """
        Composes a prometheus.yml file that configures a prometheus node
        and returns it's string
        """
        prometheus_yml = {
            'global': {
                'scrape_interval': self.scrape_interval,
                },
            'scrape_configs':[
                {
                    'job_name': 'prometheus_ring_sd',
                    'http_sd_configs': [
                        {
                            'url': f'http://{self.sd_url}:{self.sd_port}/targets',
                            'refresh_interval': self.refresh_interval
                        }
                    ],
                    'relabel_configs': [
                        {
                            'action': 'keep',
                            'source_labels': ['node_index'],
                            'regex': str(self.index)
                        }
                    ]
                }
            ],
        }
        # TODO: maybe this X-Scope-OrgID should be the cloud region
        if self.metrics_database_url is not None:
            prometheus_yml['remote_write'] = [
                {
                    'url': f'http://{self.metrics_database_url}:{self.metrics_database_port}{self.metrics_database_path}',
                    'headers': {
                        'X-Scope-OrgID': 'demo'
                    }
                }
            ]
        return yaml.dump(prometheus_yml, sort_keys=False)

    def __repr__(self):
        return f'Node {self.index}: {self.list_items()}'