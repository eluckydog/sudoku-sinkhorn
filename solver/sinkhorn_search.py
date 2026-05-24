"""Sinkhorn heuristic + constrained backtracking for hard puzzles"""
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import PUZZLE_COLLECTION, SudokuBoard
import numpy as np
import time
import sys


class SinkhornHeuristic:
    """Wraps Sinkhorn solver to produce probability heuristics"""

    def __init__(self):
        cfg = SinkhornConfig(T_start=30.0, T_end=0.001, n_iter=800, T_schedule='linear', verbose=False)
        self.inner_solver = SinkhornSudokuSolver(cfg)

    def run(self, board):
        """Solve and return (filled_grid, probability_tensor)"""
        X = self.inner_solver._init_tensor(board)
        for t in range(self.inner_solver.config.n_iter):
            T = 30.0 * (1 - t/800) + 0.001 * t/800
            for _ in range(self.inner_solver.config.n_inner):
                X = self.inner_solver._sinkhorn_step(X, T)
            X = self.inner_solver._temperature_sharpen(X, T)
            for r in range(9):
                for c in range(9):
                    v = board.grid[r][c]
                    if v != 0:
                        X[r, c, :] = 1e-10
                        X[r, c, v-1] = 1.0
        # Extract filled grid (conflict-free cells only)
        grid = [[0]*9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                if board.grid[r][c] != 0:
                    grid[r][c] = board.grid[r][c]
        for r in range(9):
            for c in range(9):
                if grid[r][c] != 0:
                    continue
                v = int(np.argmax(X[r,c,:])) + 1
                p = X[r,c,:].max()
                if p > 0.3:
                    conflict = False
                    for cc in range(9):
                        if grid[r][cc] == v: conflict = True; break
                    if not conflict:
                        for rr in range(9):
                            if grid[rr][c] == v: conflict = True; break
                    if not conflict:
                        br, bc = (r//3)*3, (c//3)*3
                        for rr in range(br, br+3):
                            for cc in range(bc, bc+3):
                                if grid[rr][cc] == v: conflict = True; break
                            if conflict: break
                    if not conflict:
                        grid[r][c] = v
        return grid, X


def backtrack_solve(grid, prob_tensor, max_nodes=50000):
    """Backtracking search using Sinkhorn probabilities as heuristic"""
    stats = {'nodes': 0}

    def get_candidates(g, r, c):
        used = set()
        for cc in range(9):
            if g[r][cc]: used.add(g[r][cc])
        for rr in range(9):
            if g[rr][c]: used.add(g[rr][c])
        br, bc = (r//3)*3, (c//3)*3
        for rr in range(br, br+3):
            for cc in range(bc, bc+3):
                if g[rr][cc]: used.add(g[rr][cc])
        return [d for d in range(1,10) if d not in used]

    def select_cell(g):
        """MRV + Sinkhorn probability ordering"""
        best_cell = None
        best_cands = None
        for r in range(9):
            for c in range(9):
                if g[r][c] == 0:
                    cands = get_candidates(g, r, c)
                    if len(cands) == 0:
                        return None, []
                    if best_cell is None or len(cands) < len(best_cands):
                        best_cell = (r, c)
                        best_cands = cands
        return best_cell, best_cands

    def search(g):
        stats['nodes'] += 1
        if stats['nodes'] > max_nodes:
            return None
        cell, cands = select_cell(g)
        if cell is None:
            if cands == []:
                return None
            sb = SudokuBoard(g)
            return g if sb.is_solved() else None
        r, c = cell
        if prob_tensor is not None:
            cands = sorted(cands, key=lambda d: -prob_tensor[r,c,d-1])
        for v in cands:
            g[r][c] = v
            result = search(g)
            if result is not None:
                return result
            g[r][c] = 0
        return None

    result = search(grid)
    return result, stats['nodes']


def hybrid_solve(board):
    """Sinkhorn reduction + heuristic backtracking (one-call API)"""
    heuristic = SinkhornHeuristic()
    filled_grid, tensor = heuristic.run(board)
    empty = sum(1 for r in range(9) for c in range(9) if filled_grid[r][c] == 0)
    if empty > 0:
        # Try from partial fill first
        result, nodes = backtrack_solve(filled_grid, tensor, max_nodes=20000)
        if result:
            return result, nodes, True
        # Fallback: from fresh clues
        fresh = [[0]*9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                fresh[r][c] = board.grid[r][c]
        result, nodes = backtrack_solve(fresh, tensor, max_nodes=50000)
        if result:
            return result, nodes, True
        return filled_grid, 0, False
    return filled_grid, 0, True


if __name__ == "__main__":
    puzzle_name = sys.argv[1] if len(sys.argv) > 1 else "ai_escargot"
    board = PUZZLE_COLLECTION[puzzle_name]
    clues = sum(1 for r in range(9) for c in range(9) if board.grid[r][c] != 0)
    print(f"Puzzle: {puzzle_name} ({clues} clues)\n")

    t0 = time.time()
    grid, nodes, solved = hybrid_solve(board)
    dt = time.time() - t0
    sb = SudokuBoard(grid)
    if solved:
        print(f"SOLVED! ({nodes} nodes, {dt:.2f}s)")
        for r in range(9):
            print(f"  {[grid[r][c] for c in range(9)]}")
    else:
        empty = sum(1 for r in range(9) for c in range(9) if grid[r][c] == 0)
        print(f"FAILED ({empty} empty, {nodes} nodes, {dt:.2f}s)")
