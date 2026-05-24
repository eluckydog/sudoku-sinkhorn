"""
demo.py - Sudoku Field complete demonstration

Run: python -m solver.demo

Pipeline:
  1. Register all 5 engines
  2. Run on 4 classic puzzles
  3. Print cross-engine comparison report
  4. Generate visualizations
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from solver.board import PUZZLE_COLLECTION
from solver.field_compare import SudokuField
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig, hybrid_solve
from solver.ga_solver import GASudokuSolver, GAConfig
from solver.sa_solver import SASudokuSolver, SAConfig
from solver.gradient_solver import GradientSudokuSolver, GradientConfig
from solver.bp_solver import BPSudokuSolver, BPConfig
from solver.visualize import plot_convergence, plot_engine_heatmap, plot_phase_diagram


def main():
    print("=" * 72)
    print("  Sudoku Field - Cross-Algorithm Constraint Landscape Analysis")
    print("=" * 72)

    # 1. Register engines
    print("\n[1/5] Registering engines...")
    sinkhorn = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=500, verbose=False))
    ga = GASudokuSolver(GAConfig(pop_size=200, max_iter=3000, patience=300, verbose=False))
    sa = SASudokuSolver(SAConfig(T_start=100.0, T_end=0.001, n_iter=3000, verbose=False))
    gradient = GradientSudokuSolver(GradientConfig(lr=0.01, n_iter=3000, verbose=False))
    bp = BPSudokuSolver(BPConfig(max_iter=100, damping=0.5, verbose=False))

    # Hybrid solver wrapper
    def hybrid_with_history(board):
        sol, meta = hybrid_solve(board)
        meta["solver"] = "sinkhorn+hybrid"
        meta["solution"] = sol
        meta["solved"] = sol.is_solved()
        return meta

    field = SudokuField()
    field.register_engine("sinkhorn_hybrid", hybrid_with_history)
    field.register_engine("sinkhorn", sinkhorn.solve_with_history)
    field.register_engine("genetic_algorithm", ga.solve_with_history)
    field.register_engine("simulated_annealing", sa.solve_with_history)
    field.register_engine("gradient_flow", gradient.solve_with_history)
    field.register_engine("belief_propagation", bp.solve_with_history)
    print(f"  Registered {len(field.engines)} engines")

    # 2. Run all puzzles
    print(f"\n[2/5] Running all puzzles (this may take a few minutes)...")
    print(f"  Puzzles: {list(PUZZLE_COLLECTION.keys())}")

    t_start = time.time()
    for pname, board in PUZZLE_COLLECTION.items():
        print(f"\n  -- {pname} (clues: {81 - board.count_empty()}) --")
        print(f"  {repr(board)}")
        for eng_name in field.engines:
            sys.stdout.write(f"    {eng_name:20s}... ")
            sys.stdout.flush()
            field.run_single(pname, board, eng_name)
            r = field.results[pname][eng_name]
            status = "PASS" if r.solved else "FAIL"
            sys.stdout.write(f"[{status}] {r.time_seconds:.2f}s, {r.n_iter} iters\n")

    total_time = time.time() - t_start
    print(f"\n  Total run time: {total_time:.1f}s")

    # 3. Report
    print(f"\n[3/5] Generating cross-engine comparison report...")
    report = field.summary_report()
    print(report)

    report_path = Path(__file__).resolve().parent.parent / "data" / "field_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"  Report saved: {report_path}")

    # 4. Visualizations
    print(f"\n[4/5] Generating visualizations...")
    figures_dir = Path(__file__).resolve().parent.parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    for pname in PUZZLE_COLLECTION:
        path = figures_dir / f"convergence_{pname}.png"
        plot_convergence(field, pname, str(path))

    plot_engine_heatmap(field, str(figures_dir / "engine_heatmap.png"))
    plot_phase_diagram(field, str(figures_dir / "phase_diagram.png"))

    # 5. Summary
    print(f"\n[5/5] Summary")
    print("=" * 72)
    solved_total = sum(1 for pname, results in field.results.items()
                       for eng_name, r in results.items() if r.solved)
    total_runs = sum(len(results) for results in field.results.values())
    print(f"  Total runs: {total_runs}, Solved: {solved_total} ({100 * solved_total / total_runs:.0f}%)")
    print(f"  Engines: {len(field.engines)}, Puzzles: {len(PUZZLE_COLLECTION)}")
    print(f"  Figures: {figures_dir}/")
    print("  First cross-engine sudoku comparison complete. New insights in report.")
    print("=" * 72)


if __name__ == "__main__":
    main()
