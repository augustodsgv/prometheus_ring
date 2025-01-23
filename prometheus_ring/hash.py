import hashlib
import os

MAX_HASH_SIZE_DIGITS = 10 ** int(os.environ.get('MAX_HASH_SIZE', '8'))
def stable_hash(key: str)->int:
    """
    returns the md5 hash of the key
    """
    hash_value = int(hashlib.sha1(key.encode()).hexdigest(), 16)
    return hash_value % MAX_HASH_SIZE_DIGITS
    