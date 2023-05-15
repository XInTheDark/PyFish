import chess

from engine_types import *

class Position:
    def __init__(self, fen=chess.STARTING_FEN):
        self.fen = fen
        self.board = chess.Board(fen)
        
        # # There is a bug where the side to move is not inferred from the FEN, so we set it manually.
        # self.board.turn = chess.WHITE if fen.split(" ")[1] == 'w' else chess.BLACK
        
    def count(self, PieceType: chess.PieceType):
        return len(self.board.pieces(PieceType, chess.WHITE))\
            + len(self.board.pieces(PieceType, chess.BLACK))
    
    def count_all(self):
        return sum([self.count(PieceType) for PieceType in chess.PIECE_TYPES])
    
    def in_check(self):
        return self.board.is_check()
    
    def checkers(self):
        return self.board.checkers()
    
    def attackers_to(self, square: chess.Square):
        return self.board.attackers(chess.WHITE, square) | self.board.attackers(chess.BLACK, square)
    
    def is_legal(self, move: chess.Move):
        return move in self.board.legal_moves
    
    def is_pseudo_legal(self, move: chess.Move):
        return move in self.board.pseudo_legal_moves
    
    def is_capture(self, move: chess.Move):
        return self.board.is_capture(move)
    
    def gives_check(self, move: chess.Move):
        return self.board.gives_check(move)
    
    def moved_piece(self, move: chess.Move):
        return self.board.piece_at(move.from_square)
    
    def captured_piece(self, move: chess.Move):
        return self.board.piece_at(move.to_square)
    
    def do_move(self, move: chess.Move):
        self.board.push(move)
        
    def undo_move(self):
        self.board.pop()
        
    def do_null_move(self):
        self.board.push(chess.Move.null())
        
    def undo_null_move(self):
        self.board.pop()
        
    
    def get_smallest_attacker(self, square: chess.Square):
        attackers = self.attackers_to(square)
        if len(attackers) == 0:
            return None
        return min(attackers, key=lambda x: piece_value(self.board.piece_type_at(x)))
    
    def see(self, square: chess.Square, color: chess.Color):
        # Static Exchange Evaluation
        value = 0
        piece = self.get_smallest_attacker(square)
        if piece:
            self.do_move(chess.Move(piece, square))
            # Do not consider captures if they lose material, therefor max zero
            value = max(0, piece_value(self.board.piece_type_at(square)) - self.see(square, not color))
            self.undo_move()
        return value
    
    def side_to_move(self):
        return self.board.turn
    
    def game_ply(self):
        return self.board.ply()
    
    def all_material(self, color=None, eg=False):
        if color is None:
            return sum([piece_value(piece_type,eg) * self.count(piece_type) for piece_type in chess.PIECE_TYPES])
        return sum([piece_value(piece_type,eg) * len(self.board.pieces(piece_type, color))
                    for piece_type in chess.PIECE_TYPES])
    
    def non_pawn_material(self, color=None, eg=False):
        if color is None:
            return sum([piece_value(piece_type,eg) * self.count(piece_type)
                        for piece_type in chess.PIECE_TYPES if piece_type != chess.PAWN])
        return sum([piece_value(piece_type,eg) * len(self.board.pieces(piece_type, color))
                    for piece_type in chess.PIECE_TYPES if piece_type != chess.PAWN])
    
    def is_endgame(self):
        # TODO: Add better handling of this
        # Meanwhile we are just using fixed thresholds.
        return self.non_pawn_material(eg=True) < Value.EndgameLimit \
            or self.count_all() - self.count(chess.PAWN) <= 5
    
def fen_from_str(s: str):
    """Parse the FEN from a string.
    For example, input: '3R4/r7/3k2P1/3p4/2pP4/1b2PK1N/5P2/8 b - - 3 48 moves d6g7',
    output: ['3R4/r7/3k2P1/3p4/2pP4/1b2PK1N/5P2/8 b - - 3 48', 'moves d6g7']
    where the first element in the list is the FEN and the remaining is the rest of the string.
    """
    
    l = s.split(" ")
    if len(l) < 6:
        raise ValueError("Invalid FEN")
    
    fen = " ".join(l[:6])
    rest = " ".join(l[6:])
    
    return [fen, rest]