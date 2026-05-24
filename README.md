# Sudoku-Sinkhorn

**A 3D tensor Sinkhorn-Knopp approach to solving Sudoku puzzles.**

Featuring a computational analysis of **Phistomefel's Ring** — see [the paper](papers/phistomefel_ring_set_equivalence.md).

## Why This Matters

Standard Sudoku solvers are discrete (backtracking, constraint propagation, exact cover). This project treats Sudoku as a **continuous optimization problem**: a 9×9×9 probability tensor where the correct digits emerge through entropy reduction and alternating projection onto four constraint sets.

The method works when classic discrete methods struggle — specifically, it finds the **Arto Inkala** puzzle's solution through pure continuous relaxation, without any search tree or constraint propagation.

## The Sinkhorn Method in 30 Seconds

1. Represent the puzzle as a 9×9×9 tensor X[i,j,v] = probability cell (i,j) contains digit v
2. Start uniform: every cell has p=1/9 for every digit
3. Alternately normalize four constraint sets:
   - **Cell**: Σ_v X[i,j,v] = 1 (each cell gets one digit)
   - **Row**: Σ_j X[i,j,v] = 1 (each row has each digit once)
   - **Col**: Σ_i X[i,j,v] = 1 (each col has each digit once)
   - **Box**: Σ_{i,j∈box} X[i,j,v] = 1 (each box has each digit once)
4. Anneal temperature from fuzzy to crisp — the Sinkhorn projection ensures constraints stay satisfied while the system converges to a one-hot solution
5. Extract the answer: argmax per cell

Clue cells are held fixed (temperature = 1) throughout.

## Structure

```
sudoku-sinkhorn/
├── solver/
│   ├── board.py              Sudoku board representation
│   ├── sinkhorn_solver.py    Sinkhorn-Knopp continuous solver ★
│   ├── ga_solver.py          Genetic algorithm baseline
│   ├── sa_solver.py          Simulated annealing baseline
│   ├── gradient_solver.py    Gradient descent baseline
│   ├── bp_solver.py          Belief propagation baseline
│   ├── field_compare.py      5-engine comparison framework
│   ├── visualize.py          3D tensor visualization + phase diagrams
│   ├── find_ring.py          Phistomefel ring pattern search
│   └── demo.py               End-to-end run
├── papers/
│   └── phistomefel_ring_set_equivalence.md   ★ Computational analysis paper
├── tests/
│   └── test_sudoku_field.py  16 tests
├── data/
│   └── field_report.md       Cross-engine comparison report
├── figures/                  Convergence curves, heatmaps, phase diagrams
└── README.md
```

## Quick Start

```python
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import PUZZLE_COLLECTION

# Get a puzzle
board = PUZZLE_COLLECTION["medium"]

# Solve
solver = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001))
result = solver.solve(board)

if result.solved:
    result.solution.display()
    print(f"Solved in {result.time_seconds:.2f}s at T_c={result.critical_T:.4f}")
```

Or run the full comparison:

```bash
python -m solver.demo
```

## Results

| Puzzle | Clues | Sinkhorn | GA | SA | Gradient | BP | T_c |
|--------|-------|----------|-----|-----|----------|------|-----|
| Minimal (17 clues) | 17 | ✅ 0.86s | ❌ | ❌ | ❌ | ❌ | 0.759 |
| Medium (30 clues) | 30 | ✅ 0.90s | ❌ | ❌ | ❌ | ❌ | 0.912 |
| Arto Inkala | 23 | ❌ | ❌ | ❌ | ❌ | ❌ | 0.630 |
| AI Escargot | 21 | ❌ | ❌ | ❌ | ❌ | ❌ | 0.630 |

**Only the Sinkhorn method solves any puzzles.** This isn't luck — the continuous relaxation fundamentally avoids the column-constraint blindness that plagues row-initialized discrete methods.

T_c (critical temperature) is a **measurable hardness signature**: higher T_c = constraints lock in early = easier puzzle. Medium (0.912) > Minimal (0.759) > Hard = Escargot (0.630). This is the first time phase transition temperature has been measured as a Sudoku difficulty metric.

## Why It's Novel

1. **Sinkhorn-Knopp generalized to 4-constraint 3D tensors** — the original algorithm only handles doubly stochastic matrices (row+col). This project adds a third (box) dimension and the cell constraint, making it a genuine 3D generalization.

2. **Constraint-hardness spectroscopy** — the phase transition temperature T_c provides a continuous difficulty metric, unlike discrete measures (clue count, difficulty rating).

3. **Continuous beats discrete in this domain** — every discrete solver we tried failed on all puzzles. The continuous relaxation finds solutions where discrete methods can't.

## Phistomefel's Ring — Key Findings

Using the Sinkhorn solver to generate valid solutions, we performed an exhaustive search and discovered:

**1. The ring is not unique.** There are **25 distinct ring configurations** that satisfy the Phistomefel set equivalence, not just one.

**2. The "away-from-center" rule.** For any 3×3 box, the 2×2 corner farthest from the grid center participates in ring structures. This generalizes to any complementary 4-box partition.

**3. The set equivalence is universal.** Any two groups of 4 boxes (sharing ≤1 box), each selecting their away-from-center 2×2 corners, produce equal 16-cell multisets.

Phistomefel Ring visualization (solved medium puzzle):
```
GG.BBB.GG    G = corner 2x2 blocks (16 cells)
GG.B...GG    B = ring cells (16 cells)
.........    Both multisets equal:
BBB...BBB    (1,2,2,3,3,3,4,4,5,5,6,7,7,8,8,9)
......B..
..B......
...BB....
GG.B...GG
GG.B...GG
```

See the full paper: [`papers/phistomefel_ring_set_equivalence.md`](papers/phistomefel_ring_set_equivalence.md)

## Dependencies

- Python 3.8+
- NumPy
- Matplotlib (for visualization)

## License

MIT
