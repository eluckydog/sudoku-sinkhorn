"""
sinkhorn_solver.py - Sinkhorn thermodynamic projection sudoku solver

Core idea:
  Treat sudoku as a 9x9x9 probability tensor X_{i,j,v}
  - Each slice (row-digit, col-digit, box-digit, cell) must be doubly stochastic
  - Alternating Sinkhorn-Knopp normalization projects onto each constraint set
  - Temperature T controls sharpness: high T=uniform, low T=one-hot
  - Annealing schedule T(t) moves from fuzzy to crisp

Reference: Sinkhorn (1964) - matrix bistochasticization via alternating normalization
Novelty: Generalization to 4-constraint 3D tensor for sudoku solving
"""

import numpy as np
from typing import Tuple, Optional, List, Callable
from dataclasses import dataclass
from solver.board import SudokuBoard, BOX_MAP


@dataclass
class SinkhornConfig:
    """Sinkhorn solver configuration"""
    T_start: float = 10.0
    T_end: float = 0.001
    T_schedule: str = "exponential"
    n_iter: int = 500
    n_inner: int = 3
    eps_converge: float = 1e-8
    record_history: bool = True
    verbose: bool = False


class SinkhornSudokuSolver:
    """Sudoku solver via Sinkhorn thermodynamic projection"""

    def __init__(self, config: Optional[SinkhornConfig] = None):
        self.config = config or SinkhornConfig()
        self.history = {"T": [], "entropy": [], "violation": []}

    def _init_tensor(self, board: SudokuBoard) -> np.ndarray:
        """Initialize 9x9x9 probability tensor

        Filled cells: one-hot
        Empty cells: uniform 1/9
        """
        X = np.ones((9, 9, 9), dtype=np.float64) / 9.0
        for r in range(9):
            for c in range(9):
                v = board.grid[r][c]
                if v != 0:
                    X[r, c, :] = 1e-10
                    X[r, c, v - 1] = 1.0
        return X

    def _temperature(self, t: int) -> float:
        """Temperature schedule"""
        ratio = t / self.config.n_iter
        if self.config.T_schedule == "linear":
            return self.config.T_start * (1 - ratio) + self.config.T_end * ratio
        elif self.config.T_schedule == "exponential":
            return self.config.T_start * (self.config.T_end / self.config.T_start) ** ratio
        elif self.config.T_schedule == "logarithmic":
            return self.config.T_start / (1 + ratio * (self.config.T_start / self.config.T_end - 1))
        return self.config.T_end

    def _temperature_sharpen(self, X: np.ndarray, T: float) -> np.ndarray:
        """Sharpen cell distributions via temperature-controlled softmax"""
        X_new = X.copy()
        for i in range(9):
            for j in range(9):
                x_ij = X[i, j, :]
                x_ij = np.exp(np.log(np.maximum(x_ij, 1e-15)) / max(T, 1e-12))
                X_new[i, j, :] = x_ij / (x_ij.sum() + 1e-15)
        return X_new

    def _sinkhorn_step(self, X: np.ndarray, T: float) -> np.ndarray:
        """One Sinkhorn projection round: alternate 4 constraint normalizations

        1. Cell constraint: sum_v X[i,j,v] = 1
        2. Row-digit constraint: sum_j X[i,j,v] = 1
        3. Col-digit constraint: sum_i X[i,j,v] = 1
        4. Box-digit constraint: sum_{(i,j) in box_b} X[i,j,v] = 1
        """
        logX = np.log(np.maximum(X, 1e-15))

        # Step 1: Cell normalization (i,j,:)
        logX = logX - np.max(logX, axis=2, keepdims=True)
        X = np.exp(logX)
        X = X / (X.sum(axis=2, keepdims=True) + 1e-15)

        # Step 2: Row-digit normalization (i,:,v)
        logX = np.log(np.maximum(X, 1e-15))
        logX = logX - np.max(logX, axis=1, keepdims=True)
        X = np.exp(logX)
        X = X / (X.sum(axis=1, keepdims=True) + 1e-15)

        # Step 3: Col-digit normalization (:,j,v)
        logX = np.log(np.maximum(X, 1e-15))
        logX = logX - np.max(logX, axis=0, keepdims=True)
        X = np.exp(logX)
        X = X / (X.sum(axis=0, keepdims=True) + 1e-15)

        # Step 4: Box-digit normalization
        for b in range(9):
            cells = BOX_MAP[b]
            idx_r = [c[0] for c in cells]
            idx_c = [c[1] for c in cells]
            box_slice = X[idx_r, idx_c, :]
            log_box = np.log(np.maximum(box_slice, 1e-15))
            log_box = log_box - np.max(log_box, axis=0, keepdims=True)
            box_slice = np.exp(log_box)
            box_slice = box_slice / (box_slice.sum(axis=0, keepdims=True) + 1e-15)
            for k, (r, c) in enumerate(cells):
                X[r, c, :] = box_slice[k, :]

        return X

    def compute_violation(self, X: np.ndarray) -> float:
        """Compute total constraint violation

        0 = all constraints satisfied
        """
        violations = 0.0
        for i in range(9):
            for j in range(9):
                violations += abs(X[i, j, :].sum() - 1.0)
        for i in range(9):
            for v in range(9):
                violations += abs(X[i, :, v].sum() - 1.0)
        for j in range(9):
            for v in range(9):
                violations += abs(X[:, j, v].sum() - 1.0)
        for b in range(9):
            cells = BOX_MAP[b]
            for v in range(9):
                total = sum(X[r, c, v] for (r, c) in cells)
                violations += abs(total - 1.0)
        return violations

    def compute_entropy(self, X: np.ndarray) -> float:
        """Compute average tensor entropy

        High entropy = uncertain (high T)
        Low entropy = certain (low T)
        """
        p = np.maximum(X, 1e-15)
        return -np.sum(p * np.log(p)) / X.size

    def extract_solution(self, X: np.ndarray) -> SudokuBoard:
        """Extract discrete solution from probability tensor"""
        grid = np.zeros((9, 9), dtype=np.int32)
        for i in range(9):
            for j in range(9):
                v = np.argmax(X[i, j, :]) + 1
                if X[i, j, :].max() > 0.3:
                    grid[i, j] = v
        return SudokuBoard(grid.tolist())

    def solve(self, board: SudokuBoard) -> Tuple[SudokuBoard, dict]:
        """Main solve function

        Returns:
            (solved board, metadata dict)
        """
        X = self._init_tensor(board)
        self.history = {"T": [], "entropy": [], "violation": []}

        for t in range(self.config.n_iter):
            T = self._temperature(t)

            for _ in range(self.config.n_inner):
                X = self._sinkhorn_step(X, T)

            X = self._temperature_sharpen(X, T)

            # Clamp known cells
            for r in range(9):
                for c in range(9):
                    v = board.grid[r][c]
                    if v != 0:
                        X[r, c, :] = 1e-10
                        X[r, c, v - 1] = 1.0

            # Record history
            if self.config.record_history and (t % 10 == 0 or t == self.config.n_iter - 1):
                self.history["T"].append(T)
                self.history["entropy"].append(self.compute_entropy(X))
                self.history["violation"].append(self.compute_violation(X))

            if self.config.verbose and t % 50 == 0:
                ent = self.compute_entropy(X)
                viol = self.compute_violation(X)
                print(f"  iter {t:4d}, T={T:.4f}, entropy={ent:.4f}, violation={viol:.4f}")

            if self.compute_violation(X) < self.config.eps_converge:
                break

        solution = self.extract_solution(X)
        metadata = {
            "converged": solution.is_solved(),
            "final_violation": self.compute_violation(X),
            "final_entropy": self.compute_entropy(X),
            "history": self.history,
            "n_iter": t + 1,
        }
        return solution, metadata

    def solve_with_history(self, board: SudokuBoard) -> dict:
        """Solve with full metadata (for field_compare)"""
        sol, meta = self.solve(board)
        meta["solver"] = "sinkhorn"
        meta["solution"] = sol
        meta["solved"] = sol.is_solved()
        return meta

    def _get_tensor(self, board: SudokuBoard) -> np.ndarray:
        """Run solver and return the final probability tensor"""
        X = self._init_tensor(board)
        for t in range(self.config.n_iter):
            T = self._temperature(t)
            for _ in range(self.config.n_inner):
                X = self._sinkhorn_step(X, T)
            X = self._temperature_sharpen(X, T)
            for r in range(9):
                for c in range(9):
                    v = board.grid[r][c]
                    if v != 0:
                        X[r, c, :] = 1e-10
                        X[r, c, v - 1] = 1.0
            if self.compute_violation(X) < self.config.eps_converge:
                break
        return X


def hybrid_solve(board: SudokuBoard) -> Tuple[SudokuBoard, dict]:
    """
    Hybrid solver: Sinkhorn continuous relaxation + heuristic backtracking.

    Phase 1: Run Sinkhorn linear-annealing solver to get probability tensor.
             Extract conflict-free partial fill from argmax probabilities.
    Phase 2: Backtrack on remaining cells using Sinkhorn probabilities
             as search heuristic (MRV + highest-probability-first).
             Falls back to solving from fresh clues if partial-fill fails.

    Solves all puzzles in the standard test suite including AI Escargot.
    """
    from solver.sinkhorn_search import hybrid_solve as _hs
    import time
    t0 = time.time()
    grid, nodes, solved = _hs(board)
    dt = time.time() - t0
    solution = SudokuBoard(grid)
    metadata = {
        "solver": "sinkhorn+hybrid",
        "solved": solved,
        "time_seconds": dt,
        "backtrack_nodes": nodes,
    }
    return solution, metadata
