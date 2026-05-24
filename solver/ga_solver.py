"""
ga_solver.py - Genetic algorithm sudoku solver

Inspired by mealpy-style GA.
Representation: 81-int vector (0=empty, 1-9=digit)
Fitness: filled cells - 2 * constraint violations
Operators: row-swap crossover, intra-row mutation
"""

import numpy as np
import random
from typing import Tuple, Optional
from dataclasses import dataclass
from solver.board import SudokuBoard, BOX_MAP


@dataclass
class GAConfig:
    """Genetic algorithm configuration"""
    pop_size: int = 200
    elite_ratio: float = 0.1
    mutation_rate: float = 0.3
    crossover_rate: float = 0.85
    max_iter: int = 5000
    patience: int = 200
    verbose: bool = False


class GASudokuSolver:
    """Genetic algorithm sudoku solver"""

    def __init__(self, config: Optional[GAConfig] = None):
        self.config = config or GAConfig()
        self.history = {"best_fitness": [], "mean_fitness": []}

    def _violation_count(self, grid: np.ndarray) -> int:
        """Count constraint violations"""
        v = 0
        for r in range(9):
            seen = set()
            for c in range(9):
                val = grid[r, c]
                if val != 0:
                    if val in seen:
                        v += 1
                    seen.add(val)
        for c in range(9):
            seen = set()
            for r in range(9):
                val = grid[r, c]
                if val != 0:
                    if val in seen:
                        v += 1
                    seen.add(val)
        for b in range(9):
            seen = set()
            for (r, c) in BOX_MAP[b]:
                val = grid[r, c]
                if val != 0:
                    if val in seen:
                        v += 1
                    seen.add(val)
        return v

    def _fitness(self, grid: np.ndarray) -> float:
        """Fitness = filled cells - 2 * violations"""
        filled = np.sum(grid > 0)
        violations = self._violation_count(grid)
        return filled - 2.0 * violations

    def _individual(self, board: SudokuBoard) -> np.ndarray:
        """Create individual by filling empty cells row-wise"""
        clues = board.as_numpy().copy()
        grid = clues.copy()
        for r in range(9):
            missing = [v for v in range(1, 10) if v not in grid[r, :]]
            random.shuffle(missing)
            for c in range(9):
                if clues[r, c] == 0:
                    grid[r, c] = missing.pop()
        return grid

    def _crossover(self, p1: np.ndarray, p2: np.ndarray, clues: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Row swap crossover"""
        r1, r2 = p1.copy(), p2.copy()
        for r in range(9):
            if random.random() < 0.5:
                mask = clues[r, :] == 0
                r1[r, mask], r2[r, mask] = r2[r, mask], r1[r, mask]
        return r1, r2

    def _mutate(self, grid: np.ndarray, clues: np.ndarray) -> np.ndarray:
        """Intra-row column swap mutation"""
        g = grid.copy()
        for r in range(9):
            if random.random() < self.config.mutation_rate:
                empty_cols = [c for c in range(9) if clues[r, c] == 0]
                if len(empty_cols) >= 2:
                    c1, c2 = random.sample(empty_cols, 2)
                    g[r, c1], g[r, c2] = g[r, c2], g[r, c1]
        return g

    def solve(self, board: SudokuBoard) -> Tuple[SudokuBoard, dict]:
        """Solve with genetic algorithm"""
        clues = board.as_numpy().copy()
        pop = [self._individual(board) for _ in range(self.config.pop_size)]

        self.history = {"best_fitness": [], "mean_fitness": []}
        best_ever = None
        best_fit = -999
        no_improve = 0
        n_elite = max(1, int(self.config.pop_size * self.config.elite_ratio))

        for gen in range(self.config.max_iter):
            fits = [self._fitness(ind) for ind in pop]
            best_idx = np.argmax(fits)

            if fits[best_idx] > best_fit:
                best_fit = fits[best_idx]
                best_ever = pop[best_idx].copy()
                no_improve = 0
            else:
                no_improve += 1

            self.history["best_fitness"].append(best_fit)
            self.history["mean_fitness"].append(np.mean(fits))

            if self.config.verbose and gen % 200 == 0:
                print(f"  GA gen {gen:4d}: best={best_fit:.1f}, mean={np.mean(fits):.1f}")

            if no_improve >= self.config.patience:
                break

            # Tournament selection
            new_pop = []
            for idx in np.argsort(fits)[-n_elite:]:
                new_pop.append(pop[idx].copy())

            while len(new_pop) < self.config.pop_size:
                t1 = random.choices(range(self.config.pop_size), weights=np.array(fits) - min(fits) + 1, k=3)
                t2 = random.choices(range(self.config.pop_size), weights=np.array(fits) - min(fits) + 1, k=3)
                p1 = pop[max(t1, key=lambda i: fits[i])]
                p2 = pop[max(t2, key=lambda i: fits[i])]

                if random.random() < self.config.crossover_rate:
                    c1, c2 = self._crossover(p1, p2, clues)
                else:
                    c1, c2 = p1.copy(), p2.copy()

                c1 = self._mutate(c1, clues)
                c2 = self._mutate(c2, clues)
                new_pop.extend([c1, c2])

            pop = new_pop[:self.config.pop_size]

        sol_grid = best_ever if best_ever is not None else pop[0]
        solution = SudokuBoard(sol_grid.tolist())
        metadata = {
            "solver": "genetic_algorithm",
            "converged": solution.is_solved(),
            "solution": solution,
            "solved": solution.is_solved(),
            "fitness": best_fit,
            "n_gen": gen + 1,
            "history": self.history,
        }
        return solution, metadata

    def solve_with_history(self, board: SudokuBoard) -> dict:
        sol, meta = self.solve(board)
        return meta
