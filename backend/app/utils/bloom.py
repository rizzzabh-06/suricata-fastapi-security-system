import hashlib

class BloomFilter:
    """Bloom filter for fast membership testing.
    Config: size and num_hashes control false positive rate.
    """
    def __init__(self, size: int = 10000, num_hashes: int = 3):
        self.size = size
        self.num_hashes = num_hashes
        self.bits = [False] * size
    
    def _hash(self, item: str, seed: int) -> int:
        h = hashlib.md5(f"{item}{seed}".encode()).hexdigest()
        return int(h, 16) % self.size
    
    def add(self, item: str):
        for i in range(self.num_hashes):
            idx = self._hash(item, i)
            self.bits[idx] = True
    
    def __contains__(self, item: str) -> bool:
        return all(self.bits[self._hash(item, i)] for i in range(self.num_hashes))
