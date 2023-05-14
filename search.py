import chess

from engine_types import *
from position import *
from search_h import *
import tt
import evaluate
import zobrist
import threads

TTtable = None  # initialised in iterative_deepening()

def futility_margin(depth: int):
    return Value(146 * depth)


best_move = None  # root move
nodes = 0

def search(pos: Position, nodeType: NodeType, ss: Stack,
           alpha: Value, beta: Value,
           depth: int, cutNode: bool):
    """Main search function. Value returned from side to move."""
    
    global nodes
    nodes += 1
    
    PvNode = nodeType == NodeType.PV or nodeType == NodeType.Root
    rootNode = nodeType == NodeType.Root
    
    # quiescence search when the depth reaches zero
    if depth <= 0:
        return qsearch(pos, NodeType.PV if PvNode else NodeType.NonPV, ss, alpha, beta, 0)
    
    assert MAX_PLY > depth > 0
    assert -Value.VALUE_INFINITE <= alpha < beta <= Value.VALUE_INFINITE
    # assert PvNode or (alpha == beta - 1)
    assert not(PvNode and cutNode)
    
    # Initialise
    ss.inCheck = inCheck = pos.in_check()
    us = pos.side_to_move()
    ss.moveCount = 0
    bestValue = -Value.VALUE_INFINITE
    maxValue = Value.VALUE_INFINITE
    bestMove = None
    eval_: Value = None
    
    # Other variables used
    improving: bool = False; improvement = 0
    
    # Step 2. Check for aborted search
    if threads.stopped():
        return evaluate.evaluate(pos)
    
    # Check for checkmate and stalemate
    if pos.board.is_checkmate():
        return -(Value.VALUE_MATE + ss.ply)
    elif pos.board.is_stalemate():
        return Value.VALUE_DRAW
    
    # Step 4. Transposition table lookup
    ttEntry = TTtable.get(pos)
    ss.ttHit = ttHit = not ttEntry.is_none()
    ttMove = ttEntry.move if ttHit else None
    ttValue = ttEntry.value if ttHit else None
    ttPv = PvNode or (ttHit and ttEntry.is_pv)
    
    # Step 6. Static evaluation
    if inCheck:
        ss.staticEval = eval_ = Value.VALUE_NONE
        
    elif ttHit:
        ss.staticEval = eval_ = ttEntry.eval
        if eval_ == Value.VALUE_NONE:
            ss.staticEval = eval_ = evaluate.evaluate(pos)
        
        # ttValue can be used as a better position evaluation
        if ttValue is not None and ttValue != Value.VALUE_NONE:
            eval_ = ttValue
            
    else:
        ss.staticEval = eval_ = evaluate.evaluate(pos)
        # Save the static eval to the TT
        TTtable.save(pos, hash_(pos), TTtable.TTEntry(hash_(pos), None, None, eval_, None, None))
    
    # Step 8. Futility pruning
    if not ttPv and depth > 9\
        and eval_ is not None\
        and eval_ - futility_margin(depth) >= beta\
        and eval_ < Value(25003)\
        and not inCheck:
        return eval_
    
    # TODO: Null move search (after I figure the Stack implementation out)
    
    for m in pos.board.legal_moves:
        ss.moveCount += 1
        extension = 0
        
        newDepth = depth - 1
        delta: Value = beta - alpha
        
        # TODO: Step 15. Extensions
        # if not rootNode and depth >= 6 and m == ttMove and abs(ttValue) < Value.VALUE_KNOWN_WIN\
        #     and ttEntry.depth >= depth - 3:
        #     singularBeta: Value = ttValue - (3 + 2 * (ttPv and not PvNode)) * depth // 2
        #     singularDepth = (depth - 1) // 2
        #
        #     value = search(pos.make_move(m), NodeType.NonPV, ss, Value(singularBeta - delta), Value(singularBeta), singularDepth, True)
        
        # Step 16. Make the move
        pos.do_move(m)
        
        r = 0
        
        if cutNode:
            r += 2
            
        # if PvNode:
        #     r -= 2
        
        elif m == ttMove:
            r -= 1
            
        # d = clamp(1, newDepth - r, newDepth + 1)
        d = newDepth
        if PvNode:
            value = -search(pos, NodeType.PV, ss, -(alpha + 1), -alpha, d, False)
            if alpha < value < beta:
                value = -search(pos, NodeType.NonPV, ss, -beta, -alpha, d, True)
        else:
            value = -search(pos, NodeType.NonPV, ss, -beta, -alpha, d, False)
        
        # Do full depth search when reduced LMR search fails high
        if value > alpha and d < newDepth:
            doDeeperSearch = value > (bestValue + 68 + 12 * (newDepth - d))
            # doEvenDeeperSearch = value > alpha + 588
            doShallowerSearch = value < bestValue + newDepth
            newDepth += doDeeperSearch - doShallowerSearch
            
            if newDepth > d:
                value = -search(pos, NodeType.NonPV, ss, -(alpha+1), -alpha, newDepth, not cutNode)
                
        # Step 19. Undo move
        pos.undo_move()
        assert Value.VALUE_INFINITE > value > -Value.VALUE_INFINITE
        
        # Step 20. Check for a new best move
        if threads.stopped():
            return Value.VALUE_ZERO
        
        if rootNode and value > alpha:
            global best_move
            best_move = m
        
        if value > bestValue:
            bestValue = value
            if value > alpha:
                bestMove = m
                if value >= beta:
                    break
                else:
                    alpha = value
                    
    
    # End of for loop
    # TODO: Step 21. Check for mate and stalemate (not needed?)
    return bestValue


def qsearch(pos: Position, nodeType: NodeType, ss: Stack,
            alpha: Value, beta: Value, depth: int):
    """Quiescence search function, called from main search with depth <= 0."""
    
    global nodes
    nodes += 1
    
    assert nodeType != NodeType.Root
    assert depth <= 0
    
    PvNode = nodeType == NodeType.PV or nodeType == NodeType.Root
    
    # Initialise
    bestMove = None
    bestValue = futilityBase = -Value.VALUE_INFINITE
    ss.inCheck = inCheck = pos.in_check()
    us = pos.side_to_move()
    
    # Check for aborted search
    if threads.stopped():
        return evaluate.evaluate(pos)
    
    # Check for checkmate and stalemate
    if pos.board.is_checkmate():
        return -(Value.VALUE_MATE + ss.ply)
    elif pos.board.is_stalemate():
        return Value.VALUE_DRAW
    
    # Transposition table lookup
    ttEntry = TTtable.get(pos)
    ttHit = not ttEntry.is_none()
    ttMove = ttEntry.move if ttHit else None
    ttValue = ttEntry.value if ttHit else None
    pvHit = ttHit and ttEntry.is_pv
    
    # At non-PV nodes we check for an early TT cutoff
    if not PvNode and ttHit and ttEntry.depth is not None and ttEntry.depth >= depth\
        and ttValue is not None and ttValue != Value.VALUE_NONE:
        return ttValue
    
    # Step 4. Static evaluation
    # if inCheck:
    if False:
        ss.staticEval = Value.VALUE_NONE
        bestValue = futilityBase = -Value.VALUE_INFINITE
    else:
        if ttHit:
            ss.staticEval = bestValue = ttEntry.eval
            if ss.staticEval == Value.VALUE_NONE:
                ss.staticEval = bestValue = evaluate.evaluate(pos)
            
            # ttValue can be used as a better position evaluation
            if ttValue is not None and ttValue != Value.VALUE_NONE:
                bestValue = ttValue
        else:
            ss.staticEval = bestValue = evaluate.evaluate(pos)
        
        if bestValue >= beta:
            # Save gathered info in transposition table
            if not ttHit:
                TTtable.save(pos, hash_(pos), TTtable.TTEntry(hash_(pos), None, bestValue, ss.staticEval,
                                                              -6, False))  # DEPTH_NONE = -6
            return bestValue
        
        if PvNode and bestValue > alpha:
            alpha = bestValue
            
        futilityBase = bestValue + 168
        
    # Step 5. Moves loop
    for m in pos.board.legal_moves:
        """Because the depth is <= 0 here, only captures,
        queen promotions, and other checks (only if depth >= DEPTH_QS_CHECKS)
        will be generated.
        """
        if not (pos.is_capture(m) or m.promotion == chess.QUEEN or pos.gives_check(m)):
            continue
            
        givesCheck = pos.gives_check(m)
        capture = pos.board.is_capture(m)
        
        # Step 6. Pruning
        if bestValue > -31508:  # VALUE_TB_LOSS_IN_MAX_PLY
            if not givesCheck and chess.Move.promotion is None and futilityBase >= -Value.VALUE_KNOWN_WIN:
                futilityValue = futilityBase + piece_value(pos.board.piece_at(m.to_square))
                if futilityValue <= alpha:
                    bestValue = max(bestValue, futilityValue)
                    continue
                if futilityBase <= alpha\
                    and pos.see(m.to_square, us) <= 0:
                    bestValue = max(bestValue, futilityBase)
                    continue
            
            # Do not search moves with bad enough SEE values
            see_value = pos.see(m.to_square, us) if capture else Value.VALUE_ZERO
            if see_value < -110:
                continue
        
        # Make the move
        pos.do_move(m)
        value = -qsearch(pos, nodeType, ss, -beta, -alpha, depth - 1)  # TODO: recursion error!
        pos.undo_move()
        
        assert Value.VALUE_INFINITE > value > -Value.VALUE_INFINITE
        
        # Step 8. Check for a new best move
        if value > bestValue:
            bestValue = value
            if value > alpha:
                bestMove = m
                if PvNode and value < beta:
                    alpha = value
                elif PvNode:
                    alpha = value
                    
        
    # Save gathered info in transposition table
    TTtable.save(pos, hash_(pos),
                 TTtable.TTEntry(hash_(pos), bestMove, bestValue, ss.staticEval,
                                 0, PvNode))  # TODO: change depth to ttDepth
        
    return bestValue
    
def iterative_deepening(rootPos: Position, max_depth: int = MAX_PLY, max_time: int = None):
    """Called by UCI command. Starts the search."""
    import time
    global nodes, TTtable
    nodes = 0  # init
    TTtable = tt.TranspositionTable(TT_SIZE)  # TODO: TT size to be added as UCI option
    
    starttime = time.time()
    if max_time:
        threads.set_time_limit(max_time / 1000)
        
    threads.init()

    for depth in range(1, max_depth + 1):
        global best_move
        best_move = None
        value = search(rootPos, NodeType.Root, Stack(), -Value.VALUE_INFINITE, Value.VALUE_INFINITE, depth, False)
        if threads.stopped():
            break

        t = int((time.time() - starttime) * 1000)

        s = f"info depth {depth} seldepth {depth} multipv 1 value cp {value} nodes {nodes} nps {1000 * nodes // t if t else 0}" \
            f" hashfull {int(TTtable.hashfull() * 1000)} tbhits 0 time {t} pv {best_move}"

        # special case: mate in x
        if value >= Value.VALUE_MATE:
            s = s.replace(f"cp {value}", f"mate {value - Value.VALUE_MATE}")
        elif value <= -Value.VALUE_MATE:
            s = s.replace(f"cp {value}", f"mate -{abs(value) - Value.VALUE_MATE}")
            
        print(s)