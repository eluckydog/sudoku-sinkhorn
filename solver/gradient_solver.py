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
        """Energy function + gradient

        E(X) = E_cell + E_row + E_col + E_box + lambda * L2

        Returns:
            (energy, gradient wrt X)
        """
        P = self._softmax_x(X)
        grad = np.zeros_like(X)

        # Cell constraint: sum_v P[i,j,v] = 1
        cell_sums = P.sum(axis=2)
        E_cell = np.sum((cell_sums - 1.0) ** 2)
        for i in range(9):
            for j in range(9):
                p = P[i, j, :]
                ds = 2 * (p.sum() - 1.0)
                grad[i, j, :] += ds * p * (1 - p)

        # Row-digit constraint: sum_j P[i,j,v] = 1
        E_row = 0.0
        for i in range(9):
            for v in range(9):
                s = P[i, :, v].sum()
                E_row += (s - 1.0) ** 2
                d = 2 * (s - 1.0)
                for j in range(9):
                    p = P[i, j, v]
                    grad[i, j, v] += d * p * (1 - p)

        # Col-digit constraint: sum_i P[i,j,v] = 1
        E_col = 0.0
        for j in range(9):
            for v in range(9):
                s = P[:, j, v].sum()
                E_col += (s - 1.0) ** 2
                d = 2 * (s - 1.0)
                for i in range(9):
                    p = P[i, j, v]
                    grad[i, j, v] += d * p * (1 - p)

        # Box-digit constraint: sum_{(i,j) in box} P[i,j,v] = 1
        E_box = 0.0
        for b in range(9):
            br, bc = b // 3 * 3, b % 3 * 3
            for v in range(9):
                s = sum(P[br + dr, bc + dc, v] for dr in range(3) for dc in range(3))
                E_box += (s - 1.0) ** 2
                d = 2 * (s - 1.0)
                for dr in range(3):
                    for dc in range(3):
                        grad[br + dr, bc + dc, v] += d * P[br + dr, bc + dc, v] * (1 - P[br + dr, bc + dc, v])

        # L2 regularization
        E_l2 = 0.5 * np.sum(X ** 2)
        grad += self.config.entropy_weight * X

        E_total = E_cell + E_row + E_col + E_box + self.config.entropy_weight * E_l2
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
