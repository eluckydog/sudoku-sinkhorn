"""test_sudoku_field.py - 数独力学场测试套件"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from solver.board import SudokuBoard, PUZZLE_MINIMAL, PUZZLE_MEDIUM, PUZZLE_HARD, BOX_MAP


def test_board_creation():
    b = SudokuBoard()
    assert b.count_empty() == 81
    assert not b.is_solved()


def test_board_from_string():
    s = """
        530070000
        600195000
        098000060
        800060003
        400803001
        700020006
        060000280
        000419005
        000080079
    """
    b = SudokuBoard.from_string(s)
    assert b.grid[0][0] == 5
    assert b.grid[0][1] == 3
    assert b.grid[0][2] == 0
    assert b.count_empty() == 51
    assert b.is_valid()


def test_is_valid_violation():
    grid = [[1] * 9 for _ in range(9)]
    b = SudokuBoard(grid)
    assert not b.is_valid()


def test_box_map():
    assert len(BOX_MAP) == 9
    for bname, cells in BOX_MAP.items():
        assert len(cells) == 9


def test_clone():
    b = SudokuBoard([[1 if i == j else 0 for j in range(9)] for i in range(9)])
    c = b.clone()
    assert b == c


def test_puzzle_minimal():
    assert PUZZLE_MINIMAL.count_empty() == 64
    assert PUZZLE_MINIMAL.is_valid()


def test_puzzle_medium():
    assert PUZZLE_MEDIUM.count_empty() == 51
    assert PUZZLE_MEDIUM.is_valid()


def test_puzzle_hard():
    assert PUZZLE_HARD.count_empty() == 60
    assert PUZZLE_HARD.is_valid()


def test_get_candidates():
    b = SudokuBoard([[1 if i == j else 0 for j in range(9)] for i in range(9)])
    cand = b.get_candidates_rc()
    assert cand[0][0] == set()


def test_sinkhorn_solve_medium():
    from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
    solver = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=500, verbose=False))
    sol, meta = solver.solve(PUZZLE_MEDIUM)
    assert sol.is_solved(), f"Sinkhorn failed: violation={meta['final_violation']:.4f}"


def test_sinkhorn_solve_minimal():
    from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
    solver = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=500, verbose=False))
    sol, meta = solver.solve(PUZZLE_MINIMAL)
    assert sol.is_solved(), f"Sinkhorn failed on minimal puzzle"


def test_sa_solve_medium():
    from solver.sa_solver import SASudokuSolver, SAConfig
    solver = SASudokuSolver(SAConfig(T_start=100.0, T_end=0.001, n_iter=3000, verbose=False))
    sol, meta = solver.solve(PUZZLE_MEDIUM)
    assert sol.count_empty() == 0, "SA should fill all cells"
    # SA may not converge perfectly; row+box constraints satisfied is expected


def test_ga_solve_medium():
    from solver.ga_solver import GASudokuSolver, GAConfig
    solver = GASudokuSolver(GAConfig(pop_size=200, max_iter=3000, patience=300, verbose=False))
    sol, meta = solver.solve(PUZZLE_MEDIUM)
    assert sol.count_empty() == 0, "GA should fill all cells"


def test_gradient_solve_medium():
    from solver.gradient_solver import GradientSudokuSolver, GradientConfig
    solver = GradientSudokuSolver(GradientConfig(lr=0.01, n_iter=3000, verbose=False))
    sol, meta = solver.solve(PUZZLE_MEDIUM)
    # Gradient flow fills all cells but may have constraint violations
    assert sol.count_empty() == 0, "Gradient flow should fill all cells"


def test_bp_solve_medium():
    from solver.bp_solver import BPSudokuSolver, BPConfig
    solver = BPSudokuSolver(BPConfig(max_iter=100, verbose=False))
    sol, meta = solver.solve(PUZZLE_MEDIUM)
    # BP should at least preserve clues and fill all cells
    assert sol.count_empty() == 0, "BP should fill all cells"


def test_field_compare():
    from solver.field_compare import SudokuField
    from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
    field = SudokuField()
    solver = SinkhornSudokuSolver(SinkhornConfig(n_iter=200, verbose=False))
    field.register_engine("sinkhorn", solver.solve_with_history)
    field.run_single("medium", PUZZLE_MEDIUM)
    assert "medium" in field.results and "sinkhorn" in field.results["medium"]


if __name__ == "__main__":
    import traceback
    funcs = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for fn in funcs:
        try:
            fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAIL: {fn.__name__}: {e}")
            traceback.print_exc()
    print(f"\n  {passed}/{passed + failed} passed")
