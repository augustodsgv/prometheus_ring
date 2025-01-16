import hashlib
import os

def hash(key: str)->int:
    """
    returns the md5 hash of the key
    """
    hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
    if 'MAX_HASH_SIZE' in os.environ:
        MAX_HASH_SIZE = int(os.environ['MAX_HASH_SIZE'])
        return hash_value % MAX_HASH_SIZE
    return hash_value
    