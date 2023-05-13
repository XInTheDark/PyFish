import chess

from engine_types import *

class Position:
    def __init__(self, fen=chess.STARTING_FEN):
        self.fen = fen
        self.board = chess.Board(fen)
        
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
    
    def all_material(self, color=None):
        if color is None:
            return sum([piece_value(piece_type) * self.count(piece_type) for piece_type in chess.PIECE_TYPES])
        return sum([piece_value(piece_type) * len(self.board.pieces(piece_type, color)) for piece_type in chess.PIECE_TYPES])
    
    def non_pawn_material(self, color=None):
        if color is None:
            return sum([piece_value(piece_type) * self.count(piece_type) for piece_type in chess.PIECE_TYPES
                        if piece_type != chess.PAWN])
        return sum([piece_value(piece_type) * len(self.board.pieces(piece_type, color)) for piece_type in chess.PIECE_TYPES
                    if piece_type != chess.PAWN])
    
    