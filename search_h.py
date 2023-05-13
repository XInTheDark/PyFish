from engine_types import *
from position import *
import zobrist

class Stack:
    pv: chess.Move = None
    ply: int = None
    currentMove: chess.Move = None
    killers = [None, None]
    staticEval: Value = None
    moveCount: int = None
    inCheck: bool = None
    ttHit: bool = None
    cutoffCnt: int = None
    

def hash_(pos: Position):
    z = zobrist.Zobrist()
    return z.hash(position=pos)
    