from position import *
import zobrist

from copy import deepcopy

class Stack:
    pv: chess.Move = None
    ply: int = 0
    currentMove: chess.Move = None
    killers = [None, None]
    staticEval: Value = None
    moveCount: int = 0
    inCheck: bool = False
    ttHit: bool = False
    cutoffCnt: int = None
    
    def __add__(self, p: int):
        self.ply += p
        return deepcopy(self)
    
    def __sub__(self, p: int):
        self.ply -= p
        return deepcopy(self)
    

def hash_(pos: Position):
    z = zobrist.Zobrist()
    return z.hash(position=pos)
    