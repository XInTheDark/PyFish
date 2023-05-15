from engine_types import *
from position import *
from evaluate_psqt import *

def evaluate(pos: Position):
    """Evaluation from side to move's POV.
    TODO: Classical eval terms from Stockfish.
    TODO: NNUE eval.
    """
    
    us = pos.side_to_move()
    them = ~us
    
    # Material eval
    MATERIAL_SCORE = pos.all_material(us) - pos.all_material(them)
    
    # PSQT eval
    eg = pos.is_endgame()
    PSQT_SCORE = psqt_score_color(pos, us, eg) - psqt_score_color(pos, them, eg)
    
    # Scale PSQT score and material score by game ply
    psqt_scale = 0.20 + 0.1 * (pos.game_ply() ** 0.5)
    psqt_scale = clamp(psqt_scale, 0.20, 1.50)
    
    MATERIAL_PSQT_SCALED = int( (2 - psqt_scale) * MATERIAL_SCORE + psqt_scale * PSQT_SCORE )
    
    return MATERIAL_PSQT_SCALED


def to_cp(v: Value) -> int:
    """Convert a value to centipawns.
    We use the SF UCI::NormalizeToPawnValue.
    """
    if Value.VALUE_TB_WIN_IN_MAX_PLY > v > Value.VALUE_TB_LOSS_IN_MAX_PLY:
        return int(100 * (v / 394))
    return int(v)