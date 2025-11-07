import hashlib

class CountMinSketch:
    """Count-Min Sketch for approximate frequency counting.
    Config: width and depth control accuracy vs memory.
    """
    def __init__(self, width: int = 1000, depth: int = 5):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
    
    def _hash(self, key: str, seed: int) -> int:
        h = hashlib.md5(f"{key}{seed}".encode()).hexdigest()
        return int(h, 16) % self.width
    
    def add(self, key: str, count: int = 1):
        for i in range(self.depth):
            idx = self._hash(key, i)
            self.table[i][idx] += count
    
    def estimate(self, key: str) -> int:
        return min(self.table[i][self._hash(key, i)] for i in range(self.depth))
