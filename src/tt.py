import chess.polyglot
import random

def _hash(pos: chess.Board):
    return chess.polyglot.zobrist_hash(pos)

class TranspositionTable:
    class TTEntry:
        # Currently the size of one entry is
        # 48 bytes as measured by getsize().
        
        # TODO: Add `bound` info.
        def __init__(self, key=None, move: chess.Move = None, value = None, eval = None,
                     depth: int = -6, is_pv: bool = None):
            self.key = key
            self.move = move
            self.value = value
            self.eval = eval
            self.depth = depth
            self.is_pv = is_pv
        
        def is_none(self):
            return self.key is None
        
        def getsize(self):
            import sys
            return sys.getsizeof(self)
    
    def __init__(self, size: int):
        # size is given in megabytes. convert to entries:
        entries = int(size * 1024 * 1024 / 48)
        self.size = entries
        # TODO: Limit size of table. Currently entries is NOT used functionally; the table can be arbitrarily large.
        
        self.table = {}  # use dictionary for now
    
    def hashfull(self):
        # total = cnt = 0
        # for entry in random.sample(self.table, 30000):
        #     total += 1
        #     if not entry.is_none():
        #         cnt += 1
        # return int(1000 * cnt / total)
        return int(1000 * len(self.table) / self.size)
    
    def hash(self, pos: chess.Board):
        # return _hash(pos) % self.size
        return pos.fen()  # TODO: proper hashing and TT system
    
    def get(self, key):
        # returns TTEntry() as default value.
        return self.table.get(key, self.TTEntry())
    
    def save(self, key, entry: TTEntry):
        entry.key = key
        self.table[key] = entry
    
    def clear(self):
        self.table = {}
    
    def __str__(self):
        return str(self.table)


tt = TranspositionTable(10)