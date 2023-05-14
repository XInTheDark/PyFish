from enum import Enum, auto

import chess

MAX_PLY = 246
TT_SIZE = 2**15

class Value:
    def __init__(self, value: int):
        self.value = value
        
    VALUE_ZERO = 0
    VALUE_DRAW = 0
    VALUE_KNOWN_WIN = 10000
    VALUE_MATE = 32000
    VALUE_INFINITE = 32001
    VALUE_NONE = 32002
    
    PawnValueMg = 126
    PawnValueEg = 208
    KnightValueMg = 781
    KnightValueEg = 854
    BishopValueMg = 825
    BishopValueEg = 915
    RookValueMg = 1276
    RookValueEg = 1380
    QueenValueMg = 2538
    QueenValueEg = 2682
    
    MidgameLimit = 15258
    EndgameLimit = 5365
    
    def __neg__(self):
        return Value(-self.value)
    
    def __eq__(self, other):
        if type(other) == int:
            return self.value == other
        return self.value == other.value
    
    def __lt__(self, other):
        if type(other) == int:
            return self.value < other
        return self.value < other.value
    
    def __gt__(self, other):
        if type(other) == int:
            return self.value > other
        return self.value > other.value

    def __ge__(self, other):
        if type(other) == int:
            return self.value >= other
        return self.value >= other.value
    def __le__(self, other):
        if type(other) == int:
            return self.value <= other
        return self.value <= other.value
    
    def __sub__(self, other: int):
        return Value(self.value - other)
    def __add__(self, other: int):
        return Value(self.value + other)
    def __mul__(self, other: int):
        return Value(self.value * other)
    def __truediv__(self, other: int):
        return Value(self.value // other)
    
    def __int__(self):
        return self.value
    

class NodeType(Enum):
    PV = auto()
    NonPV = auto()
    Root = auto()
    

def piece_value(t: chess.PieceType, eg=False):
    if t == chess.PAWN:
        return Value.PawnValueEg if eg else Value.PawnValueMg
    elif t == chess.KNIGHT:
        return Value.KnightValueEg if eg else Value.KnightValueMg
    elif t == chess.BISHOP:
        return Value.BishopValueEg if eg else Value.BishopValueMg
    elif t == chess.ROOK:
        return Value.RookValueEg if eg else Value.RookValueMg
    elif t == chess.QUEEN:
        return Value.QueenValueEg if eg else Value.QueenValueMg
    elif t == chess.KING:
        return Value.VALUE_INFINITE
    return Value.VALUE_ZERO


def clamp(v, min_, max_):
    if v < min_:
        return min_
    elif v > max_:
        return max_
    return v