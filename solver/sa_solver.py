"""
sa_solver.py - Simulated annealing sudoku solver

Inspired by Hermes BPD (Boltzmann Policy Distribution) temperature framework.
Core: Metropolis-Hastings acceptance with temperature annealing schedule.
"""

import numpy as np
import math
import random
from typing import Tuple, Optional
from dataclasses import dataclass
from solver.board import SudokuBoard, BOX_MAP


@dataclass
class SAConfig:
    """Simulated annealing configuration"""
    T_start: float = 100.0
    T_end: float = 0.001
    T_schedule: str = "exponential"
    n_iter: int = 10000
    steps_per_T: int = 50
    verbose: bool = False


class SASudokuSolver:
    """Simulated annealing sudoku solver"""

    def __init__(self, config: Optional[SAConfig] = None):
        self.config = config or SAConfig()
        self.history = {"T": [], "energy": [], "accept_rate": []}

    def _energy(self, grid: np.ndarray) -> float:
        """Energy = count of constraint violations (lower is better)"""
        violations = 0.0
        for r in range(9):
            counts = np.bincount(grid[r, :].astype(int), minlength=10)[1:]
            violations += np.sum(np.maximum(counts - 1, 0))
        for c in range(9):
            counts = np.bincount(grid[:, c].astype(int), minlength=10)[1:]
            violations += np.sum(np.maximum(counts - 1, 0))
        for b in range(9):
            br, bc = b // 3 * 3, b % 3 * 3
            cells = [grid[br + dr, bc + dc] for dr in range(3) for dc in range(3)]
            counts = np.bincount(np.array(cells).astype(int), minlength=10)[1:]
            violations += np.sum(np.maximum(counts - 1, 0))
        return violations

    def _init_state(self, board: SudokuBoard) -> Tuple[np.ndarray, np.ndarray]:
        """Initialize: fill each row with missing digits randomly"""
        clues = board.as_numpy().copy()
        grid = clues.copy()
        for r in range(9):
            missing = [v for v in range(1, 10) if v not in grid[r, :]]
            random.shuffle(missing)
            for c in range(9):
                if grid[r, c] == 0:
                    grid[r, c] = missing.pop()
        return grid, clues

    def _propose(self, grid: np.ndarray, clues: np.ndarray) -> np.ndarray:
        """Propose new state: swap two empty cells in the same row"""
        g = grid.copy()
        r = random.randrange(9)
        empty_cols = [c for c in range(9) if clues[r, c] == 0]
        if len(empty_cols) >= 2:
            c1, c2 = random.sample(empty_cols, 2)
            g[r, c1], g[r, c2] = g[r, c2], g[r, c1]
        return g

    def _temperature(self, t: int) -> float:
        ratio = t / self.config.n_iter
        if self.config.T_schedule == "linear":
            return self.config.T_start * (1 - ratio) + self.config.T_end * ratio
        return self.config.T_start * (self.config.T_end / self.config.T_start) ** ratio

    def solve(self, board: SudokuBoard) -> Tuple[SudokuBoard, dict]:
        """Solve with simulated annealing"""
        grid, clues = self._init_state(board)
        current_energy = self._energy(grid)
        best_grid = grid.copy()
        best_energy = current_energy

        self.history = {"T": [], "energy": [], "accept_rate": []}
        accepted = 0
        total_steps = self.config.n_iter * self.config.steps_per_T

        for t in range(self.config.n_iter):
            T = self._temperature(t)
            step_accepted = 0

            for _ in range(self.config.steps_per_T):
                new_grid = self._propose(grid, clues)
                new_energy = self._energy(new_grid)
                delta_e = new_energy - current_energy

                if delta_e < 0 or random.random() < math.exp(-delta_e / max(T, 1e-12)):
                    grid = new_grid
                    current_energy = new_energy
                    step_accepted += 1
                    if current_energy < best_energy:
                        best_energy = current_energy
                        best_grid = grid.copy()

            accept_rate = step_accepted / self.config.steps_per_T
            accepted += step_accepted

            if t % 50 == 0:
                self.history["T"].append(T)
                self.history["energy"].append(best_energy)
                self.history["accept_rate"].append(accept_rate)

            if self.config.verbose and t % 200 == 0:
                print(f"  SA iter {t:4d}, T={T:.4f}, energy={best_energy:.1f}, accept={accept_rate:.2f}")

            if best_energy == 0:
                break

        solution = SudokuBoard(best_grid.tolist())
        metadata = {
            "solver": "simulated_annealing",
            "converged": solution.is_solved(),
            "solution": solution,
            "solved": solution.is_solved(),
            "final_energy": best_energy,
            "n_iter": t + 1,
            "accept_rate_total": accepted / total_steps,
            "history": self.history,
        }
        return solution, metadata

    def solve_with_history(self, board: SudokuBoard) -> dict:
        sol, meta = self.solve(board)
        return meta
