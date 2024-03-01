import chess
import chess.engine

import utils as utils
from ucioption import option

from typing import *
import math

from collections import deque

# Constants
MAX_DEPTH = 245
MAX_PLY = 246
MAX_MOVES = 256

VALUE_INFINITE = 32001
VALUE_NONE = 32002
VALUE_MATE = 32000

VALUE_MATE_IN_MAX_PLY = VALUE_MATE - MAX_PLY
VALUE_MATED_IN_MAX_PLY = -VALUE_MATE_IN_MAX_PLY

VALUE_TB_WIN_IN_MAX_PLY = VALUE_MATE_IN_MAX_PLY - MAX_PLY - 1
VALUE_TB_LOSS_IN_MAX_PLY = -VALUE_TB_WIN_IN_MAX_PLY

VALUE_DRAW = VALUE_ZERO = 0


class RunningAverage:
    max_count = 1024
    default_value = 0
    total = 0
    count = 0
    values = deque()

    def __init__(self, max_count: int = 1024, default_value: int = 0):
        assert max_count > 0
        self.max_count = max_count
        self.default_value = default_value

    def add(self, value):
        self.total += value
        self.count += 1
        if self.count > self.max_count:
            self.total -= self.values.popleft()  # removes the oldest value
            self.count -= 1
        self.values.append(value)

    def value(self):
        return self.total / self.count if self.count > 0 else self.default_value

    def clear(self):
        self.total = 0
        self.count = 0
        self.values.clear()

    def __str__(self):
        return str(self.value())

    def __int__(self):
        return int(self.value())

class NodeType:
    NonPV = 0
    PV = 1
    Root = 2
    

class Stack:
    pv: chess.Move = None  # TODO: Proper PV handling
    currentMove: chess.Move = None
    excludedMove: chess.Move = None
    ply = 0
    staticEval = None
    moveCount = None
    inCheck = False
    cutoffCnt = 0
    ttPv = False
    

class RootMove:
    move: chess.Move = None
    score = -VALUE_INFINITE
    averageScore = -VALUE_INFINITE
    previousScore = -VALUE_INFINITE
    uciScore = -VALUE_INFINITE
    is_lowerbound = is_upperbound = False
    # TODO: pv
    
    def __init__(self, move: chess.Move):
        self.move = move

# RootMoves is just an array of RootMoves.

def stable_sort(rootMoves: list):
    # the built-in sort() is stable by default. Sort by score first, if they are equal, sort by previousScore.
    rootMoves.sort(key=lambda x: (x.score, x.previousScore), reverse=True)
    

# chess specific utils
def has_non_pawn_material(pos: chess.Board):
    return pos.knights or pos.bishops or pos.rooks or pos.queens

def has_pawn_material(pos: chess.Board):
    return pos.pawns


# general utils
def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

def mate_in(ply):
    return VALUE_MATE - ply

def mated_in(ply):
    return -VALUE_MATE + ply

def not_none(value):
    return value is not None and value != VALUE_NONE


# search specific functions

# Init reductions table
reductions = [0] * MAX_MOVES
for i in range(1, MAX_MOVES):
    reductions[i] = int(18.79 * math.log(i))

def reduction(i, d, mn) -> int:
    reductionScale = reductions[d] * reductions[mn]
    return reductionScale // 1024 + (not i and reductionScale > 863) + 1

# UCI stuff
def uci_pv(depth, score, nodes, hashfull, time, rootMoves):
    time = int(max(time * 1000, 1))
    nps = int(nodes * 1000 / time)
    
    bestMove = rootMoves[0].move.uci()
    upperbound, lowerbound = rootMoves[0].is_upperbound, rootMoves[0].is_lowerbound
    
    s = (f"info depth {depth} score cp {score} {'upperbound ' if upperbound else 'lowerbound ' if lowerbound else ''}"
         f"nodes {nodes} nps {nps} hashfull {hashfull} time {time} pv {bestMove}")
    return s