import position, search, threads, benchmark
from engine_types import *

def move_to_uci(move: chess.Move):
    """Convert a chess.Move object to a UCI string."""
    return move.uci()

def uci_to_move(uci: str):
    """Convert a UCI string to a chess.Move object."""
    return chess.Move.from_uci(uci)


def uci():
    """Start the UCI interface."""
    print("PyFish chess engine")
    pos = position.Position()
    while True:
        command = input()
        if command == "uci":
            print(f"id name PyFish")
            print(f"id author Muzhen Gaming")
            print("uciok")
        elif command == "isready":
            print("readyok")
        elif command == "ucinewgame":
            pos = position.Position()
        elif command == "position startpos":
            pos = position.Position()
        elif command.startswith("position startpos moves"):
            moves = command.split("position startpos moves ")[1].split(" ")
            for move in moves:
                pos.board.push(uci_to_move(move))
        elif command.startswith("position fen") and "moves" in command:
            fen = command.split(" ")[2]
            moves = command.split("moves ")[1].split(" ")
            pos = position.Position(fen)
            for move in moves:
                pos.board.push(uci_to_move(move))
        elif command.startswith("position fen"):
            fen = command.split(" ")[2]
            pos = position.Position(fen)
        elif command.startswith("go"):
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "movetime":
                movetime = int(command.split(" ")[2])
            else:
                movetime = None
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "depth":
                depth = int(command.split(" ")[2])
            else:
                depth = MAX_PLY
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "infinite":
                depth = MAX_PLY
                movetime = None
            
            # we do not support time controls yet.
            # we also do not support pondering.
            # nodes and mate may be added in the future.
            
            search.iterative_deepening(pos, depth, movetime)
        
        elif command == "quit":
            break
        elif command == "stop":
            # when this command is issued, we must stop searching immediately
            # and return the best move found so far ("bestmove" output).
            threads.stop_search()
        elif command == "bench":
            benchmark.benchmark()