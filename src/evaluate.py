import utils
import chess
import random


pieceValues = [0, 208, 781, 825, 1276, 2538, 0]
NormalizeToPawnValue = 328

from psqt import *

TEMPO_VALUE = 20


def evaluate(pos: chess.Board):
    """Evaluation from side to move's POV.
    TODO: Classical eval terms from Stockfish.
    TODO: NNUE eval.
    """
    
    us = pos.turn
    them = ~us
    
    # Material eval
    MATERIAL_SCORE = all_material(pos, us) - all_material(pos, them)
    
    # PSQT eval
    PSQT_SCORE = psqt_score_color(pos, us) - psqt_score_color(pos, them)
    
    return MATERIAL_SCORE + PSQT_SCORE


def to_uci(v) -> int:
    """Convert a value to centipawns.
    We use the SF UCI::NormalizeToPawnValue.
    """
    return int(v * 100 / NormalizeToPawnValue)


def all_material(pos, color=None):
    if color is None:
        return all_material(pos, chess.WHITE) + all_material(pos, chess.BLACK)
    
    return sum(pieceValues[pos.piece_type_at(sq)] for sq in pos.pieces(chess.PAWN, color)) \
        + sum(pieceValues[pos.piece_type_at(sq)] for sq in pos.pieces(chess.KNIGHT, color)) \
        + sum(pieceValues[pos.piece_type_at(sq)] for sq in pos.pieces(chess.BISHOP, color)) \
        + sum(pieceValues[pos.piece_type_at(sq)] for sq in pos.pieces(chess.ROOK, color)) \
        + sum(pieceValues[pos.piece_type_at(sq)] for sq in pos.pieces(chess.QUEEN, color))