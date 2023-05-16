import position, search, threads, benchmark
from engine_types import *
from ucioption import *

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
            print(f"id author the PyFish developers (see AUTHORS file)\n")
            # UCI options
            print(options_str())
            print("uciok")
        elif command == "isready":
            print("readyok")
        elif command == "ucinewgame":
            pos = position.Position()
        elif command == "position startpos":
            pos = position.Position()
        elif command.startswith("position startpos moves"):
            try:
                moves = command.split("position startpos moves ")[1].split(" ")
            except IndexError:
                moves = []
            for move in moves:
                pos.board.push(uci_to_move(move))
        elif command.startswith("position fen") and "moves" in command:
            # remove 'position fen '
            s = ' '.join(command.split(" ")[2:])
            fen = position.fen_from_str(s)[0]
            moves = position.fen_from_str(s)[1].split()[1:]
            pos = position.Position(fen)
            for move in moves:
                pos.board.push(uci_to_move(move))
        elif command.startswith("position fen"):
            s = ' '.join(command.split(" ")[2:])
            fen = position.fen_from_str(s)[0]
            pos = position.Position(fen)
        elif command.startswith("go"):
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "movetime":
                movetime = int(command.split(" ")[2])
            else:
                movetime = None
                
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "nodes":
                nodes = int(command.split(" ")[2])
            else:
                nodes = None
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "depth":
                depth = int(command.split(" ")[2])
            else:
                depth = MAX_PLY
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "infinite":
                depth = MAX_PLY
                movetime = None
            
            # we do not support time controls yet.
            # we also do not support pondering.
            
            search.iterative_deepening(pos, depth, movetime, nodes)
        
        elif command == "quit":
            break
        elif command == "stop":
            # when this command is issued, we must stop searching immediately
            # and return the best move found so far ("bestmove" output).
            threads.stop_search()
        elif command == "bench":
            benchmark.benchmark()
            
        # option setting
        elif command.startswith("setoption"):
            # FORMAT: name <id> value <x>
            c = command.split()
            if not c[1] == "name":
                continue
            try:
                value_index = c.index("value")
            except ValueError:
                # Type = button
                value_index = c.__len__()
            name = " ".join(c[2:value_index])
            value = " ".join(c[value_index+1:])
            
            # set the option
            setoption(name, value)