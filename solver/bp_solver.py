"""
bp_solver.py - Belief propagation sudoku solver

Inspired by Hermes BPD (factor graph + message passing).
Core: Factor graph with 81 variable nodes (cells) and 27 factor nodes (rows/cols/boxes)
Messages propagate via sum-product algorithm with damping.
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from solver.board import SudokuBoard, BOX_MAP


@dataclass
class BPConfig:
    """Belief propagation configuration"""
    max_iter: int = 100
    damping: float = 0.5
    tol: float = 1e-6
    verbose: bool = False


class BPSudokuSolver:
    """Belief propagation sudoku solver"""

    def __init__(self, config: Optional[BPConfig] = None):
        self.config = config or BPConfig()
        self.history = {"max_diff": [], "entropy": []}

    def solve(self, board: SudokuBoard) -> Tuple[SudokuBoard, dict]:
        """Solve with belief propagation

        Returns:
            (solved board, metadata)
        """
        # Initialize log-belief: zeros for uniform prior, -inf for fixed clues
        belief = np.zeros((9, 9, 9), dtype=np.float64)
        for r in range(9):
            for c in range(9):
                v = board.grid[r][c]
                if v != 0:
                    belief[r, c, :] = -1e10
                    belief[r, c, v - 1] = 0.0

        # Initialize messages
        mu_row = np.zeros((9, 9, 9), dtype=np.float64)
        mu_col = np.zeros((9, 9, 9), dtype=np.float64)
        mu_box = np.zeros((9, 9, 9), dtype=np.float64)

        self.history = {"max_diff": [], "entropy": []}

        for iteration in range(self.config.max_iter):
            new_mu_row = self._update_row_messages(belief, mu_row, mu_col, mu_box)
            new_mu_col = self._update_col_messages(belief, mu_col, mu_row, mu_box)
            new_mu_box = self._update_box_messages(belief, mu_box, mu_row, mu_col)

            # Damping
            mu_row = (1 - self.config.damping) * new_mu_row + self.config.damping * mu_row
            mu_col = (1 - self.config.damping) * new_mu_col + self.config.damping * mu_col
            mu_box = (1 - self.config.damping) * new_mu_box + self.config.damping * mu_box

            new_belief = self._update_belief(board, mu_row, mu_col, mu_box)
            diff = np.max(np.abs(new_belief - belief))
            belief = new_belief

            if iteration % 10 == 0:
                ent = self._compute_entropy(belief)
                self.history["max_diff"].append(diff)
                self.history["entropy"].append(ent)

            if self.config.verbose and iteration % 20 == 0:
                print(f"  BP iter {iteration:3d}, diff={diff:.2e}")

            if diff < self.config.tol and iteration > 10:
                break

        # Extract solution
        grid = np.zeros((9, 9), dtype=np.int32)
        for r in range(9):
            for c in range(9):
                grid[r, c] = np.argmax(belief[r, c, :]) + 1

        solution = SudokuBoard(grid.tolist())
        metadata = {
            "solver": "belief_propagation",
            "converged": solution.is_solved(),
            "solution": solution,
            "solved": solution.is_solved(),
            "n_iter": iteration + 1,
            "final_entropy": self._compute_entropy(belief),
            "history": self.history,
        }
        return solution, metadata

    def _update_row_messages(self, belief, mu_row, mu_col, mu_box):
        """Row factor message update"""
        mu = np.zeros_like(mu_row)
        for r in range(9):
            for v in range(9):
                for j in range(9):
                    mu[r, v, j] = belief[r, j, v] - mu_col[r, j, v] - mu_box[r, j, v]
        return mu

    def _update_col_messages(self, belief, mu_col, mu_row, mu_box):
        """Column factor message update"""
        mu = np.zeros_like(mu_col)
        for c in range(9):
            for v in range(9):
                for r in range(9):
                    mu[c, v, r] = belief[r, c, v] - mu_row[r, v, c] - mu_box[r, c, v]
        # Transpose to (r=9, c=9, v=9) format
        result = np.zeros((9, 9, 9))
        for c in range(9):
            for v in range(9):
                for r in range(9):
                    result[r, c, v] = mu[c, v, r]
        return result

    def _update_box_messages(self, belief, mu_box, mu_row, mu_col):
        """Box factor message update"""
        mu = np.zeros((9, 9, 9))
        for b in range(9):
            br, bc = b // 3 * 3, b % 3 * 3
            cells = [(br + dr, bc + dc) for dr in range(3) for dc in range(3)]
            for v in range(9):
                for ci, (r, c) in enumerate(cells):
                    mu[r, c, v] = belief[r, c, v] - mu_row[r, v, c] - mu_col[r, c, v]
        return mu

    def _update_belief(self, board, mu_row, mu_col, mu_box):
        """Update belief = clue_prior + sum of incoming messages"""
        belief = np.zeros((9, 9, 9), dtype=np.float64)
        for r in range(9):
            for c in range(9):
                v_clue = board.grid[r][c]
                for v in range(9):
                    belief[r, c, v] = mu_row[r, v, c] + mu_col[r, c, v] + mu_box[r, c, v]
                if v_clue != 0:
                    belief[r, c, :] = -1e10
                    belief[r, c, v_clue - 1] = 0.0
                # Softmax normalization
                b = belief[r, c, :]
                b = b - np.max(b)
                exp_b = np.exp(b)
                s = exp_b.sum() + 1e-15
                belief[r, c, :] = np.log(exp_b / s)
        return belief

    def _compute_entropy(self, belief):
        """Compute average entropy from log-belief"""
        p = np.exp(belief)
        p = p / (p.sum(axis=2, keepdims=True) + 1e-15)
        eps = 1e-15
        return -np.sum(p * np.log(p + eps)) / p.size

    def solve_with_history(self, board: SudokuBoard) -> dict:
        sol, meta = self.solve(board)
        return meta
