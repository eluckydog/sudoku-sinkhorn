"""
field_compare.py - Cross-engine comparison and constraint landscape analysis

Core features:
  1. Run all 5 engines on the same puzzle
  2. Record convergence trajectories (energy/entropy/temperature/time)
  3. Compute "difficulty spectrum": cross-engine convergence differences
  4. Generate analysis report: where is the difficulty? (global vs algorithm-blindness)

This layer produces new insights, not new solvers.
"""

import time
import numpy as np
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from solver.board import SudokuBoard, PUZZLE_COLLECTION


@dataclass
class EngineResult:
    """Result of one engine on one puzzle"""
    solver_name: str
    solved: bool
    time_seconds: float
    n_iter: int
    final_energy: float
    history: Dict[str, list] = field(default_factory=dict)
    solution: Optional[SudokuBoard] = None


@dataclass
class DifficultySignature:
    """Puzzle difficulty characteristics"""
    puzzle_name: str
    n_clues: int
    all_solved: bool
    n_engines_solved: int
    solve_times: Dict[str, float]
    fastest_engine: str
    slowest_engine: str
    convergence_gap: float
    sinkhorn_critical_temp: Optional[float]
    entropy_trajectories: Dict[str, list]
    energy_trajectories: Dict[str, list]


class SudokuField:
    """Cross-engine comparison arena"""

    def __init__(self):
        self.engines = {}
        self.results: Dict[str, Dict[str, EngineResult]] = {}
        self.difficulty_signatures: Dict[str, DifficultySignature] = {}

    def register_engine(self, name: str, solver_fn, config=None):
        self.engines[name] = {"fn": solver_fn, "config": config}

    def run_single(self, puzzle_name: str, board: SudokuBoard, engine_name: str = None):
        """Run specified or all engines on a single puzzle"""
        if puzzle_name not in self.results:
            self.results[puzzle_name] = {}

        targets = {engine_name: self.engines[engine_name]} if engine_name else self.engines

        for name, eng in targets.items():
            t0 = time.time()
            try:
                meta = eng["fn"](board)
                elapsed = time.time() - t0
                self.results[puzzle_name][name] = EngineResult(
                    solver_name=name,
                    solved=meta.get("solved", False),
                    time_seconds=elapsed,
                    n_iter=meta.get("n_iter", 0),
                    final_energy=meta.get("final_energy", meta.get("final_violation", 999)),
                    history=meta.get("history", {}),
                    solution=meta.get("solution"),
                )
            except Exception as e:
                elapsed = time.time() - t0
                self.results[puzzle_name][name] = EngineResult(
                    solver_name=name, solved=False, time_seconds=elapsed,
                    n_iter=0, final_energy=999, history={},
                )

    def run_all(self):
        """Run all engines on all registered puzzles"""
        for name, board in PUZZLE_COLLECTION.items():
            self.run_single(name, board)
        self._compute_difficulty_signatures()

    def _compute_difficulty_signatures(self):
        """Compute difficulty signature for each puzzle"""
        for pname, engine_results in self.results.items():
            board = PUZZLE_COLLECTION[pname]

            solved_count = sum(1 for r in engine_results.values() if r.solved)
            solve_times = {k: v.time_seconds for k, v in engine_results.items() if v.solved}
            fastest = min(solve_times, key=solve_times.get) if solve_times else "none"
            slowest = max(solve_times, key=solve_times.get) if solve_times else "none"

            iters = [v.n_iter for v in engine_results.values() if v.solved and v.n_iter > 0]
            conv_gap = max(iters) / min(iters) if len(iters) >= 2 else 1.0

            # Sinkhorn critical temperature
            critical_T = None
            if "sinkhorn" in engine_results and engine_results["sinkhorn"].history:
                h = engine_results["sinkhorn"].history
                if "T" in h and "entropy" in h and len(h["T"]) > 2:
                    ent = np.array(h["entropy"])
                    d_ent = np.diff(ent)
                    if len(d_ent) > 0:
                        phase_idx = np.argmin(d_ent)
                        if phase_idx < len(h["T"]):
                            critical_T = h["T"][phase_idx]

            entropy_traj = {}
            energy_traj = {}
            for eng_name, result in engine_results.items():
                if result.history:
                    h = result.history
                    if "entropy" in h:
                        entropy_traj[eng_name] = h["entropy"]
                    if "energy" in h:
                        energy_traj[eng_name] = h["energy"]
                    if "violation" in h:
                        energy_traj[eng_name] = h["violation"]
                    if "best_fitness" in h:
                        energy_traj[eng_name] = h["best_fitness"]

            self.difficulty_signatures[pname] = DifficultySignature(
                puzzle_name=pname,
                n_clues=81 - board.count_empty(),
                all_solved=solved_count == len(self.engines),
                n_engines_solved=solved_count,
                solve_times=solve_times,
                fastest_engine=fastest,
                slowest_engine=slowest,
                convergence_gap=conv_gap,
                sinkhorn_critical_temp=critical_T,
                entropy_trajectories=entropy_traj,
                energy_trajectories=energy_traj,
            )

    def summary_report(self) -> str:
        """Generate cross-engine comparison report"""
        if not self.difficulty_signatures:
            self._compute_difficulty_signatures()

        lines = []
        lines.append("=" * 72)
        lines.append("  SUDOKU FIELD - Cross-Engine Comparison Report")
        lines.append("=" * 72)

        for pname, sig in self.difficulty_signatures.items():
            board = PUZZLE_COLLECTION[pname]
            lines.append(f"\n{'-' * 72}")
            lines.append(f"  Puzzle: {pname} (clues: {sig.n_clues})")
            lines.append(f"{'-' * 72}")
            lines.append(f"  Board:")
            for row in repr(board).split("\n"):
                lines.append(f"    {row}")

            lines.append(f"\n  > Results:")
            for engine_name, result in self.results[pname].items():
                status = "PASS" if result.solved else "FAIL"
                lines.append(f"    [{status}] {engine_name:20s} | "
                           f"time={result.time_seconds:.3f}s | "
                           f"iters={result.n_iter:5d} | "
                           f"E={result.final_energy:.2e}")

            if sig.sinkhorn_critical_temp is not None:
                lines.append(f"\n  > Sinkhorn phase transition: T_c = {sig.sinkhorn_critical_temp:.4f}")

            if sig.convergence_gap > 2.0:
                lines.append(f"\n  > Convergence gap (max/min iters): {sig.convergence_gap:.1f}x")
                lines.append(f"    Hint: large gap = algorithm-specific difficulty exists")

            if not sig.all_solved:
                unsolved = [k for k, v in self.results[pname].items() if not v.solved]
                lines.append(f"\n  > Unsolved engines: {', '.join(unsolved)}")
                lines.append(f"    Hint: this puzzle has global-level difficulty")

            lines.append("")

        lines.append("=" * 72)
        lines.append("  NEW INSIGHTS")
        lines.append("=" * 72)
        lines.append("")
        self._append_cognition_insights(lines)

        return "\n".join(lines)

    def _append_cognition_insights(self, lines: list):
        """Extract insights from comparisons"""
        if not self.difficulty_signatures:
            return

        any_global = any(not sig.all_solved and sig.n_engines_solved == 0
                        for sig in self.difficulty_signatures.values())
        any_blind = any(not sig.all_solved and sig.n_engines_solved > 0
                       for sig in self.difficulty_signatures.values())

        lines.append("  [Insight 1] Difficulty classification: global vs algorithm-blind")
        if any_global:
            lines.append("    Puzzles unsolved by ALL engines -> global difficulty")
        if any_blind:
            lines.append("    Puzzles solved by SOME engines -> algorithm-blind spots exist")
        lines.append("")

        for pname, sig in self.difficulty_signatures.items():
            if sig.sinkhorn_critical_temp is not None:
                lines.append(f"  [Insight 2] Sinkhorn phase transition mapping")
                lines.append(f"    '{pname}' critical T_c = {sig.sinkhorn_critical_temp:.4f}")
                lines.append(f"    Higher T_c = constraints lock in early -> easier puzzle")
                lines.append(f"    Lower T_c = needs deep annealing -> harder puzzle")
                break

        lines.append("")
        lines.append("  [Insight 3] Engine convergence profiles")
        for pname, sig in self.difficulty_signatures.items():
            if sig.convergence_gap > 2:
                lines.append(f"    '{pname}': convergence speed gap {sig.convergence_gap:.1f}x "
                           f"(fast={sig.fastest_engine}, slow={sig.slowest_engine})")

    def get_engine_results(self) -> Dict:
        return {
            "results": self.results,
            "signatures": self.difficulty_signatures,
        }
