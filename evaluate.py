from engine_types import *
from position import *

def evaluate(pos: Position):
    """Evaluation from side to move's POV.
    TODO: Psqt eval.
    TODO: Classical eval terms from Stockfish.
    TODO: NNUE eval.
    """
    
    us = pos.side_to_move()
    them = ~us
    
    # Material eval
    MATERIAL_SCORE = pos.all_material(us) - pos.all_material(them)
    
    return MATERIAL_SCORE
