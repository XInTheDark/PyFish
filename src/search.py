from time import time as time_now

import evaluate
import tt
from search_h import *
from timeman import *
from utils import printf

STOP_SEARCH = False
IS_SEARCHING = False

prevBestMove = None

timemanObj: Time = None
useTimeMan = False
movetimeLimit = nodesLimit = startTime = None

searchStack = [Stack() for _ in range(MAX_PLY + 10)]
for _ in range(7, MAX_PLY + 10):
    searchStack[i].ply = i - 7  # Search starts at ss_idx = 7.

nodes_searched = 0

ttTable: tt.TranspositionTable = None

# thread exclusive things
nmpMinPly = 0
rootDepth = 0
rootMoves: List[RootMove] = []

def iterative_deepening(rootPos: chess.Board, depth: int = MAX_DEPTH,
           nodes: int = None, movetime: int = None, timeman: Time = Time()):
    """
    Search a position by tracing the PV.

    param MAX_ITERS: Maximum number of iterations
    param nodes: Maximum number of *total* nodes across all iterations
    param time: Maximum time *per move*
    """
    
    global STOP_SEARCH, IS_SEARCHING
    global searchStack, nodes_searched
    global timemanObj, useTimeMan, movetimeLimit, nodesLimit, startTime
    global ttTable
    global nmpMinPly, rootMoves, rootDepth
    
    timemanObj = timeman
    movetimeLimit = movetime
    nodesLimit = nodes
    
    STOP_SEARCH = False
    IS_SEARCHING = True
    
    # initialise timeman object
    assert timemanObj is not None
    timemanObj.init(rootPos.turn, rootPos.ply())
    if movetime:
        timemanObj.optTime = timemanObj.maxTime = movetime
    optTime = timemanObj.optTime
    maxTime = timemanObj.maxTime
    
    useTimeMan = optTime != 0 or maxTime != 0
    startTime = time_now()
    
    # init more stuff
    alpha = -VALUE_INFINITE
    beta = VALUE_INFINITE
    bestValue = -VALUE_INFINITE
    value = VALUE_NONE
    bestMove = None
    us = rootPos.turn
    nodes_searched = 0
    
    searchStack = [Stack() for _ in range(MAX_PLY + 10)]
    for _ in range(7, MAX_PLY + 10):
        searchStack[i].ply = i - 7  # Search starts at ss_idx = 7.
    ss_idx = 7
    
    # init TT
    ttTable = tt.TranspositionTable(option("Hash"))
    
    # init thread exclusive things
    nmpMinPly = 0
    rootDepth = 1
    
    for move in rootPos.legal_moves:
        rootMoves.append(RootMove(move=move))
        
    # special case for no legal moves
    if len(rootMoves) == 0:
        printf("bestmove (none)")
        return
    
    while rootDepth <= depth and not STOP_SEARCH:
        
        # update previousScore
        for rm in rootMoves:
            rm.previousScore = rm.score
            
        failedHighCnt = 0
        delta = 10
        
        while True:
            adjustedDepth = max(1, rootDepth - failedHighCnt - 1)
            bestValue = search(NodeType.Root, rootPos, ss_idx, alpha, beta, adjustedDepth, False)
            
            # Sort root moves
            stable_sort(rootMoves)
            
            bestRm = rootMoves[0]  # always found since we have handled no legal moves case
            bestMove = bestRm.move
            
            if STOP_SEARCH:
                break
                
            printf(uci_pv(rootDepth, bestValue, nodes_searched, ttTable.hashfull(), time_now() - startTime, rootMoves)
                   )
            
            if bestValue <= alpha:
                beta = (alpha + beta) // 2
                alpha = max(bestValue - delta, -VALUE_INFINITE)
                failedHighCnt = 0
            elif bestValue >= beta:
                beta = min(bestValue + delta, VALUE_INFINITE)
                failedHighCnt += 1
            else:
                break
            
            delta += delta // 3
            assert alpha >= -VALUE_INFINITE and beta <= VALUE_INFINITE
        
        rootDepth += 1
        
        if STOP_SEARCH:
            printf(uci_pv(rootDepth, bestValue, nodes_searched, ttTable.hashfull(), time_now() - startTime, rootMoves)
                   )
        
        # time management code
        # TODO: make better (port some from sf)
        if useTimeMan and not STOP_SEARCH:
            totalTime = optTime
            if time_now() - startTime > totalTime \
                    or (movetimeLimit and time_now() - startTime > movetimeLimit) \
                    or (nodesLimit and nodes_searched > nodesLimit):
                STOP_SEARCH = True
                
    # end of while loop
    IS_SEARCHING = False
    printf(f"bestmove {bestMove}")
    return
        

def search(nodetype, pos, ss_idx, alpha, beta, depth, cutNode):
    global searchStack, ttTable, nodes_searched
    global nmpMinPly
    
    ss = searchStack[ss_idx]
    
    PvNode = nodetype == NodeType.PV or nodetype == NodeType.Root
    rootNode = nodetype == NodeType.Root
    
    # qsearch if depth <= 0
    if depth <= 0:
        return qsearch(nodetype, pos, ss_idx, alpha, beta)
    
    assert alpha >= -VALUE_INFINITE and beta <= VALUE_INFINITE
    assert PvNode or alpha == beta - 1
    assert 0 < depth < MAX_PLY
    assert not (PvNode and cutNode)
    
    tte = posKey = None
    ttMove = move = None
    searchStack[ss_idx + 1].excludedMove = bestMove = None
    searchStack[ss_idx + 2].cutoffCnt = 0
    extension = newDepth = 0
    bestValue = value = ttValue = eval = maxValue = probCutBeta = VALUE_NONE
    givesCheck = improving = priorCapture = False
    capture = ttCapture = False
    
    # initialise node
    ss.inCheck = bool(pos.checkers())
    us = pos.turn
    moveCount = ss.moveCount = 0
    bestValue = -VALUE_INFINITE
    maxValue = VALUE_INFINITE
    
    # TODO: continuation history stuff
    
    # check for time
    if nodes_searched % 512 == 0:
        if (useTimeMan and time_now() - startTime > timemanObj.maxTime) \
                or (movetimeLimit and time_now() - startTime > movetimeLimit) \
                or (nodesLimit and nodes_searched > nodesLimit):
            stop_search()
        
    if not rootNode:
        # Check for aborted search and immediate draw
        if STOP_SEARCH or pos.can_claim_draw() or pos.is_insufficient_material() \
                or ss.ply >= MAX_PLY:
            return evaluate.evaluate(pos) if (ss.ply >= MAX_PLY and not ss.inCheck) \
                else VALUE_DRAW
    
        # Mate distance pruning
        alpha = max(mated_in(ss.ply), alpha)
        beta = min(mate_in(ss.ply + 1), beta)
        if alpha >= beta:
            return alpha
    
    assert 0 <= ss.ply <= MAX_PLY
    
    # TT lookup
    excludedMove = ss.excludedMove
    posKey = ttTable.hash(pos)
    tte = ttTable.get(posKey)
    ss.ttHit = not tte.is_none()
    ttValue = tte.value if ss.ttHit else VALUE_NONE
    ttMove = tte.move if ss.ttHit else None
    if not excludedMove:
        ss.ttPv = PvNode or (ss.ttHit and tte.is_pv)
    
    # At non-PV nodes we check for an early TT cutoff
    if ss.ttHit and not PvNode and not excludedMove and tte.depth >= depth and not_none(ttValue):
        if pos.halfmove_clock < 90:
            return ttValue
    
    # Static evaluation
    if ss.ttHit:
        ss.staticEval = eval = tte.eval
        if not not_none(eval):
            ss.staticEval = eval = evaluate.evaluate(pos)
            
        # ttValue can be used as a better position evaluation
        if not_none(ttValue):  # TODO: Add bound to TT
            eval = ttValue
    
    else:
        ss.staticEval = eval = evaluate.evaluate(pos)
        # Save evaluation to TT
        ttTable.save(posKey, ttTable.TTEntry(is_pv=ss.ttPv, eval=eval))
        
    # Calculate improving
    staticEval_2, staticEval_4 = searchStack[ss_idx - 2].staticEval, searchStack[ss_idx - 4].staticEval
    improving = (ss.staticEval > staticEval_2) if not_none(staticEval_2) \
        else (not_none(staticEval_4) and ss.staticEval > staticEval_4)
        
    # Futility pruning: child node
    if not ss.ttPv and depth < 11 and eval - 117 * depth >= beta \
        and eval < VALUE_MATE_IN_MAX_PLY and not ttMove:
        return (eval + beta) // 2 if beta > VALUE_TB_LOSS_IN_MAX_PLY else eval
    
    # Null move search (WITHOUT verification search)
    if not PvNode and searchStack[ss_idx - 1] != chess.Move.null() and eval >= beta and eval >= ss.staticEval \
        and ss.staticEval >= beta - 21 * depth + 330 and not excludedMove and has_non_pawn_material(pos) \
        and ss.ply >= nmpMinPly and beta > VALUE_TB_LOSS_IN_MAX_PLY:
        
        R = min((eval - beta) // 154, 6) + depth // 3 + 4
        ss.currentMove = chess.Move.null()
        
        pos.push(chess.Move.null())
        nullValue = -search(NodeType.NonPV, pos, ss_idx + 1, -beta, -beta + 1, depth - R, ~cutNode)
        pos.pop()
        
        if beta <= nullValue < VALUE_TB_WIN_IN_MAX_PLY:
            if nmpMinPly or depth < 16:
                return nullValue
            nmpMinPly = ss.ply + 3 * depth // 4
            
            v = search(NodeType.NonPV, pos, ss_idx, beta - 1, beta, depth - R, False)
            nmpMinPly = 0
            
            if v >= beta:
                return nullValue
        
    # Internal iterative reductions
    if PvNode and not ttMove:
        depth -= 2
    
    if depth <= 0:
        return qsearch(NodeType.PV, pos, ss_idx, alpha, beta)
    
    if cutNode and depth >= 8 and not ttMove:
        depth -= 2
    
    # moves loop
    value = bestValue
    moveCountPruning = False
    
    for move in pos.legal_moves:  # TODO: Move histories in move generation (move ordering)
        if move == excludedMove:
            continue
            
        ss.moveCount = moveCount = moveCount + 1
        
        extension = 0
        capture = pos.is_capture(move)
        givesCheck = pos.gives_check(move)
        
        newDepth = depth - 1
        
        r = reduction(improving, depth, moveCount)
        
        # Pruning at shallow depth
        if not rootNode and has_non_pawn_material(pos) and bestValue > VALUE_TB_LOSS_IN_MAX_PLY:
            lmrDepth = newDepth - r
            # TODO: SEE pruning
            
            if not (capture or givesCheck):
                # Futility pruning: parent node
                if not ss.inCheck and lmrDepth < 15 and ss.staticEval + 104 + 121 * lmrDepth <= alpha:
                    continue
        
        # Extensions
        if ss.ply < rootDepth * 2:
            # SE search
            if not rootNode and move == ttMove and not excludedMove and depth >= 4 + ss.ttPv \
                    and abs(ttValue) < VALUE_TB_WIN_IN_MAX_PLY and tte.depth >= depth - 3:
                singularMargin = 99 + 65 * (ss.ttPv and not PvNode)
                singularBeta = ttValue - singularMargin * depth // 64
                singularDepth = newDepth // 2
                
                ss.excludedMove = move
                value = search(NodeType.NonPV, pos, ss_idx, singularBeta - 1, singularBeta, singularDepth, cutNode)
                ss.excludedMove = None
                
                if value < singularBeta:
                    extension = 1
                    if not PvNode and value < singularBeta - 60:
                        # TODO: double extension guard.
                        extension = 2
                        depth += (depth < 16)
                 
                elif singularBeta >= beta:
                    return singularBeta
                
                # Negative extensions
                elif ttValue >= beta or cutNode:
                    extension = -2
                elif ttValue <= value:
                    extension = -1
        
        # Add extension to new depth
        newDepth += extension
        ss.currentMove = move
        
        # Make move, and increment node count
        nodes_searched += 1
        pos.push(move)
        
        # Reduction adjustments
        if ss.ttPv and not_none(ttValue):
            r -= 1 + (ttValue > alpha) + (tte.depth >= depth)
        
        if cutNode:
            r += 2 - (ss.ttHit and tte.depth >= depth and ss.ttPv)
            
        if ttCapture:
            r += 1
        
        if PvNode:
            r -= 1
        
        if move == searchStack[ss_idx - 4].currentMove:
            r += 2
            
        if searchStack[ss_idx + 1].cutoffCnt > 3:
            r += 1
        
        # Late moves reduction (LMR)
        if depth >= 2 and moveCount > (1 + rootNode):
            d = max(1, min(newDepth - r, newDepth + 1))
            
            value = -search(NodeType.NonPV, pos, ss_idx + 1, -(alpha + 1), -alpha, d, True)
            
            if value > alpha and d < newDepth:
                doDeeperSearch = value > bestValue + 49 + 2 * newDepth
                doShallowerSearch = value < bestValue + newDepth
                
                newDepth += doDeeperSearch - doShallowerSearch
                
                if newDepth > d:
                    value = -search(NodeType.NonPV, pos, ss_idx + 1, -(alpha + 1), -alpha, newDepth, ~cutNode)
        
        # Full depth search when LMR is skipped
        elif not PvNode or moveCount > 1:
            if not ttMove:
                r += 2
            value = -search(NodeType.NonPV, pos, ss_idx + 1, -(alpha + 1), -alpha, newDepth - (r > 3), ~cutNode)
        
        # TODO: update PV for PvNodes (do this after PV handling)
        if PvNode and (moveCount == 1 or value > alpha):
            value = -search(NodeType.PV, pos, ss_idx + 1, -beta, -alpha, newDepth, False)
        
        # Undo move
        pos.pop()
        
        assert -VALUE_INFINITE < value < VALUE_INFINITE
        
        # If thread.stop: return VALUE_ZERO
        if STOP_SEARCH:
            return VALUE_ZERO
        
        # Check for a new best move
        
        # TODO: Move ordering
        if rootNode:
            rm = find_rm(move)
            rm.averageScore = value if rm.averageScore == -VALUE_INFINITE else (rm.averageScore + 2 * value) // 3
            
            if moveCount == 1 or value > alpha:
                rm.score = rm.uciScore = value
                rm.is_lowerbound = rm.is_upperbound = False
                
                if value >= beta:
                    rm.is_lowerbound = True
                    rm.uciScore = beta
                elif value <= alpha:
                    rm.is_upperbound = True
                    rm.uciScore = alpha
            else:
                rm.score = -VALUE_INFINITE
        
        if value > bestValue:
            bestValue = value
            
            if value > alpha:
                bestMove = move
                # TODO: update PV
                
                if value >= beta:  # fail high
                    ss.cutoffCnt += 1 + (not ttMove)
                    break
                else:
                    # Reduce other moves if we have found at least one score improvement
                    if 2 < depth < 13 and beta < 13652 and value > -12761:
                        depth -= 2
                        
                    assert depth > 0
                    alpha = value
        
    # end of moves loop
    
    # Check for mate and stalemate
    assert moveCount or not ss.inCheck or excludedMove or len(pos.legal_moves) == 0
    
    if moveCount == 0:
        if excludedMove:
            bestValue = alpha
        else:
            bestValue = mated_in(ss.ply) if ss.inCheck else VALUE_DRAW
    
    if PvNode:
        bestValue = min(bestValue, maxValue)  # TODO: simplify away maxValue (it's only used with tablebases)
    
    if bestValue <= alpha:
        ss.ttPv = ss.ttPv or (searchStack[ss_idx - 1].ttPv and depth > 3)
    
    # Save to TT
    ttTable.save(posKey, ttTable.TTEntry(value=bestValue, is_pv=ss.ttPv, depth=depth,
                                         move=bestMove, eval=eval))  # TODO: add bounds, ply
    
    assert -VALUE_INFINITE < bestValue < VALUE_INFINITE
    
    return bestValue


def qsearch(nodetype, pos, ss_idx, alpha, beta, depth=0):
    global searchStack, ttTable, nodes_searched
    global nmpMinPly
    
    ss = searchStack[ss_idx]
    
    # handle rootNode case since qsearch can be called from root search
    if nodetype == NodeType.Root:
        nodetype = NodeType.PV
    
    PvNode = nodetype == NodeType.PV
    
    assert -VALUE_INFINITE <= alpha < beta <= VALUE_INFINITE
    assert PvNode or alpha == beta - 1
    assert depth <= 0
    
    tte = posKey = None
    ttMove = move = bestMove = None
    ttDepth = 0
    searchStack[ss_idx + 2].cutoffCnt = 0
    bestValue = value = ttValue = eval = futilityValue = futilityBase = -VALUE_INFINITE
    pvHit = givesCheck = capture = False
    us = pos.turn
    
    # initialise node
    ss.inCheck = bool(pos.checkers())
    moveCount = 0
    
    # Check for immediate draw or maximum ply reached
    if pos.can_claim_draw() or pos.is_insufficient_material() \
            or ss.ply >= MAX_PLY:
        return evaluate.evaluate(pos) if (ss.ply >= MAX_PLY and not ss.inCheck) \
            else VALUE_DRAW
    
    assert 0 <= ss.ply <= MAX_PLY
    
    ttDepth = 0 if ss.inCheck or depth == 0 else -1  # DEPTH_QS_CHECKS, DEPTH_QS_NO_CHECKS in SF
    
    # TT lookup
    posKey = ttTable.hash(pos)
    tte = ttTable.get(posKey)
    ss.ttHit = not tte.is_none()
    ttValue = tte.value if ss.ttHit else VALUE_NONE
    ttMove = tte.move if ss.ttHit else None
    pvHit = ss.ttHit and tte.is_pv
    
    # At non-PV nodes we check for an early TT cutoff
    if ss.ttHit and not PvNode and tte.depth >= ttDepth and not_none(ttValue):
        return ttValue
    
    # Static evaluation
    if ss.ttHit:
        ss.staticEval = bestValue = tte.eval
        if not not_none(eval):
            ss.staticEval = bestValue = evaluate.evaluate(pos)
            
        # ttValue can be used as a better position evaluation
        if not_none(ttValue):  # TODO: Add bound to TT
            bestValue = ttValue
    
    else:
        # use previous static eval with a different sign
        if searchStack[ss_idx - 1].currentMove == chess.Move.null():
            ss.staticEval = bestValue = -searchStack[ss_idx - 1].staticEval
        else:
            ss.staticEval = bestValue = evaluate.evaluate(pos)
            
    # Stand pat. Return immediately if static value is at least beta
    if bestValue >= beta:
        if not ss.ttHit:
            # Save evaluation to TT
            ttTable.save(posKey, ttTable.TTEntry(is_pv=False, value=bestValue, 
                                                 eval=ss.staticEval))  # TODO: add lowerbound
        return beta
    
    if bestValue > alpha:
        alpha = bestValue
        
    futilityBase = ss.staticEval + 206
    
    quietCheckEvasions = 0
    
    # Generate only captures and queen promotions
    # and checks only if depth == 0 (this is taken from SF DEPTH_QS_CHECKS = 0)
    
    for move in pos.legal_moves:  # TODO: Move histories in move generation (move ordering)
        givesCheck = pos.gives_check(move)
        capture = pos.is_capture(move)
        isQueenPromotion = move.promotion == chess.QUEEN
        
        if not (capture or isQueenPromotion or (givesCheck and depth == 0)):
            continue
            
        moveCount += 1
        
        # Pruning
        if bestValue > VALUE_TB_LOSS_IN_MAX_PLY and has_non_pawn_material(pos):
            # Futility pruning
            if not givesCheck and futilityBase > VALUE_TB_LOSS_IN_MAX_PLY and not isQueenPromotion:
                # TODO: moveCount pruning after move ordering is implemented
                
                # captures only
                capturedPieceValue = evaluate.pieceValues[pos.piece_type_at(move.to_square)]
                futilityValue = futilityBase + capturedPieceValue
                
                if futilityValue <= alpha:
                    bestValue = max(bestValue, futilityValue)
                    continue    
                
            # TODO: SEE
            
            # Quiet check evasions
            if quietCheckEvasions > 1:
                break
                
        
        ss.currentMove = move
        quietCheckEvasions += not capture and ss.inCheck
        
        # Make move, and increment node count
        nodes_searched += 1
        
        pos.push(move)
        value = -qsearch(nodetype, pos, ss_idx + 1, -beta, -alpha, depth - 1)
        pos.pop()
        
        assert -VALUE_INFINITE < value < VALUE_INFINITE
        
        # Check for a new best move
        if value > bestValue:
            bestValue = value
            
            if value > alpha:
                bestMove = move
                
                if value < beta:
                    alpha = value
                else:  # fail high
                    break
        
    # end of moves loop
    
    # Check for mate
    if pos.is_checkmate():
        return mated_in(ss.ply)
    
    # Save to TT
    ttTable.save(posKey, ttTable.TTEntry(is_pv=pvHit, value=bestValue, depth=ttDepth,
                                         move=bestMove, eval=ss.staticEval))  # TODO: add bounds, ply
    
    assert -VALUE_INFINITE < bestValue < VALUE_INFINITE
    
    return bestValue
    

def stop_search():
    global STOP_SEARCH, IS_SEARCHING
    
    STOP_SEARCH = True
    

# search utilities
def find_rm(move: chess.Move):
    global rootMoves
    for rm in rootMoves:
        if rm.move == move:
            return rm
    return None