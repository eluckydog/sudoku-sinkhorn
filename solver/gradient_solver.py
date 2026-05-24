"""
gradient_solver.py - Continuous gradient flow sudoku solver

Inspired by Hermes QBM (Quantum Boltzmann Machine) energy landscape.
Core: Encode sudoku constraints as differentiable energy function E(X)
Evolve via gradient descent dx/dt = -nabla E(x) in continuous space
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from solver.board import SudokuBoard, BOX_MAP


@dataclass
class GradientConfig:
    """Gradient flow configuration"""
    lr: float = 0.01
    n_iter: int = 5000
    entropy_weight: float = 0.01
    patience: int = 200
    verbose: bool = False


class GradientSudokuSolver:
    """Continuous gradient flow sudoku solver"""

    def __init__(self, config: Optional[GradientConfig] = None):
        self.config = config or GradientConfig()
        self.history = {"energy": [], "grad_norm": []}

    def _init_continuous(self, board: SudokuBoard) -> np.ndarray:
        """Initialize continuous tensor R^{9x9x9}"""
        X = np.random.randn(9, 9, 9) * 0.1
        for r in range(9):
            for c in range(9):
                v = board.grid[r][c]
                if v != 0:
                    X[r, c, :] = -10.0
                    X[r, c, v - 1] = 10.0
        return X

    def _softmax_x(self, X: np.ndarray) -> np.ndarray:
        """Softmax along last axis to get probabilities"""
        x = X - np.max(X, axis=2, keepdims=True)
        exp_x = np.exp(x)
        return exp_x / (exp_x.sum(axis=2, keepdims=True) + 1e-15)

    def _energy_fn(self, X: np.ndarray) -> Tuple[float, np.ndarray]:
        """Energy function + gradient (correct softmax Jacobian, vectorized)

        E(X) = E_row + E_col + E_box + lambda * L2

        Uses the full softmax Jacobian:
            dP_k / dX_l = P_k * (delta_{k,l} - P_l)

        Returns:
            (energy, gradient wrt X)
        """
        P = self._softmax_x(X)
        grad = np.zeros_like(X)

        # Row-digit constraint: sum_j P[i,j,v] = 1  (vectorized)
        # P: (9,9,9) -> col_sums: (9,9) sum over col dim 1
        col_sums = P.sum(axis=1)       # (9,9): row i, digit v
        row_residual = col_sums - 1.0  # (9,9)
        E_row = np.sum(row_residual ** 2)
        # dEdP: (9,9,9) broadcast over col dim
        dEdP_row = 2.0 * row_residual[:, np.newaxis, :]  # (9,1,9)
        dot_row = np.sum(P * dEdP_row, axis=2, keepdims=True)  # (9,9,1)
        grad += P * (dEdP_row - dot_row)

        # Col-digit constraint: sum_i P[i,j,v] = 1  (vectorized)
        row_sums = P.sum(axis=0)       # (9,9): col j, digit v
        col_residual = row_sums - 1.0  # (9,9)
        E_col = np.sum(col_residual ** 2)
        dEdP_col = 2.0 * col_residual[np.newaxis, :, :]  # (1,9,9)
        dot_col = np.sum(P * dEdP_col, axis=2, keepdims=True)  # (9,9,1)
        grad += P * (dEdP_col - dot_col)

        # Box-digit constraint: sum_{(i,j) in box} P[i,j,v] = 1  (vectorized)
        # Build box selector: for each box (9), 9 cells -> (9,9) mask per cell? No.
        # Reshape: (9,9,9) -> (3,3,3,3,9) for box grouping
        P_boxes = P.reshape(3, 3, 3, 3, 9)  # (row_block, col_block, row_in_box, col_in_box, digit)
        box_sums = P_boxes.sum(axis=(2, 3))  # (3,3,9): box_block_row, box_block_col, digit
        box_residual = box_sums - 1.0        # (3,3,9)
        E_box = np.sum(box_residual ** 2)
        # dEdP broadcast to each cell in box: (1,1,3,3,9)
        dEdP_box = 2.0 * box_residual[:, :, np.newaxis, np.newaxis, :]  # (3,3,1,1,9)
        dot_box = np.sum(P_boxes * dEdP_box, axis=4, keepdims=True)     # (3,3,3,3,1)
        grad_box = P_boxes * (dEdP_box - dot_box)                       # (3,3,3,3,9)
        grad += grad_box.reshape(9, 9, 9)

        # L2 regularization
        E_l2 = 0.5 * np.sum(X ** 2)
        grad += self.config.entropy_weight * X

        E_total = E_row + E_col + E_box + self.config.entropy_weight * E_l2
        return E_total, grad

    def solve(self, board: SudokuBoard) -> Tuple[SudokuBoard, dict]:
        """Solve with continuous gradient flow"""
        X = self._init_continuous(board)
        best_X = X.copy()
        best_energy = float("inf")
        no_improve = 0

        self.history = {"energy": [], "grad_norm": []}

        for t in range(self.config.n_iter):
            energy, grad = self._energy_fn(X)
            X -= self.config.lr * grad

            # Clamp known cells
            for r in range(9):
                for c in range(9):
                    v = board.grid[r][c]
                    if v != 0:
                        X[r, c, :] = -10.0
                        X[r, c, v - 1] = 10.0

            if energy < best_energy:
                best_energy = energy
                best_X = X.copy()
                no_improve = 0
            else:
                no_improve += 1

            if t % 100 == 0:
                self.history["energy"].append(energy)
                self.history["grad_norm"].append(np.linalg.norm(grad))

            if self.config.verbose and t % 500 == 0:
                print(f"  GF iter {t:4d}, E={energy:.2f}, grad_norm={np.linalg.norm(grad):.2f}")

            if no_improve >= self.config.patience:
                break

        P = self._softmax_x(best_X)
        grid = np.zeros((9, 9), dtype=np.int32)
        for i in range(9):
            for j in range(9):
                grid[i, j] = np.argmax(P[i, j, :]) + 1

        solution = SudokuBoard(grid.tolist())
        metadata = {
            "solver": "gradient_flow",
            "converged": solution.is_solved(),
            "solution": solution,
            "solved": solution.is_solved(),
            "final_energy": best_energy,
            "n_iter": t + 1,
            "history": self.history,
        }
        return solution, metadata

    def solve_with_history(self, board: SudokuBoard) -> dict:
        sol, meta = self.solve(board)
        return meta
