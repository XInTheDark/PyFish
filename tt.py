from engine_types import *
from position import *
import zobrist

class TranspositionTable:
    class TTEntry:
        def __init__(self, key=None, move: chess.Move=None, value: Value=None, eval: Value=None,
                     depth: int=None, is_pv: bool=None):
            self.key = key
            self.move = move
            self.value = value
            self.eval = eval
            self.depth = depth
            self.is_pv = is_pv
            
        def is_none(self):
            return self.key is None
    def __init__(self, size: int):
        self.size = size
        self.table = [self.TTEntry() for i in range(self.size)]
        self.zobrist = zobrist.Zobrist()
        
    def hashfull(self):
        return sum([1 for entry in self.table if not entry.is_none()])
    
    def hash(self, pos: Position):
        return self.zobrist.hash(pos) % self.size
    
    def get(self, pos: Position):
        return self.table[self.hash(pos)]
    
    def save(self, pos: Position, posKey: int, entry: TTEntry):
        self.table[posKey] = entry
    
    def clear(self):
        self.table = [None for i in range(self.size)]
    
    def __str__(self):
        return str(self.table)
    
    