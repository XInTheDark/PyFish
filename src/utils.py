import math

import chess
import chess.engine

from ucioption import *

def pv_to_uci(pv):
    s = ""
    for move in pv:
        s += f"{move.uci()} "

    # remove the last space
    return s[:-1]


def nodes_to_str(nodes: int):
    """@:return: a string of the number of nodes in millions"""
    return f"{nodes / 1000000:.2f}M"


def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)


def printf(s: str):
    print(s, flush=True)
