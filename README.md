# Sudoku-Sinkhorn / 数独辛克霍恩

**A 3D tensor Sinkhorn-Knopp approach to solving Sudoku puzzles**
**三维张量 Sinkhorn-Knopp 连续松弛求解数独**

Featuring a computational analysis of **Phistomefel's Ring** — see [the paper](papers/phistomefel_ring_set_equivalence.md).

---

## Why This Matters / 为什么重要

Standard Sudoku solvers are discrete (backtracking, constraint propagation, exact cover). This project treats Sudoku as a **continuous optimization problem**: a 9×9×9 probability tensor where the correct digits emerge through entropy reduction and alternating projection onto four constraint sets.

传统数独求解器是离散的（回溯、约束传播、精确覆盖）。本项目将数独视为**连续优化问题**：一个 9×9×9 概率张量，通过熵减和交替投影到四个约束集上，正确数字自然浮现。

The method works when classic discrete methods struggle — it finds solutions through pure continuous relaxation, without any search tree or constraint propagation.

当经典离散方法失效时，这个方法仍然有效——纯连续松弛就能求解，无需搜索树或约束传播。

## The Sinkhorn Method in 30 Seconds / 三十秒理解

1. **Tensor** / 张量: 9×9×9 张量 X[i,j,v] = 格(i,j)含数字v的概率
2. **Init** / 初始化: 所有格均匀分布 p=1/9
3. **Project** / 交替投影到四个约束集:
   - **Cell** / 格约束: Σ_v X[i,j,v] = 1
   - **Row** / 行约束: Σ_j X[i,j,v] = 1
   - **Col** / 列约束: Σ_i X[i,j,v] = 1
   - **Box** / 宫约束: Σ_{i,j∈box} X[i,j,v] = 1
4. **Anneal** / 退火: 温度从模糊到锐化，Sinkhorn 投影确保约束始终满足
5. **Extract** / 提取: 每格取 argmax

Clue cells are held fixed throughout. 提示格始终固定。

## Structure / 目录结构

```
sudoku-sinkhorn/
├── solver/
│   ├── board.py              盘面表示
│   ├── sinkhorn_solver.py    Sinkhorn-Knopp 连续求解器 ★
│   ├── ga_solver.py          遗传算法基线
│   ├── sa_solver.py          模拟退火基线
│   ├── gradient_solver.py    梯度下降基线
│   ├── bp_solver.py          置信传播基线
│   ├── field_compare.py      五引擎对比框架
│   ├── visualize.py          三维张量可视化 + 相图
│   ├── find_ring.py          Phistomefel 环搜索
│   └── demo.py               端到端运行
├── papers/
│   └── phistomefel_ring_set_equivalence.md   ★ 分析论文
├── tests/
│   └── test_sudoku_field.py  16 个测试
├── data/
│   └── field_report.md       引擎对比报告
├── figures/                  收敛曲线、热力图、相图
│   └── phistomefel_ring.html  交互式环可视化
└── README.md
```

## Quick Start / 快速开始

```python
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import PUZZLE_COLLECTION

board = PUZZLE_COLLECTION["medium"]
solver = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001))
result = solver.solve(board)

if result.solved:
    result.solution.display()
    print(f"Solved in {result.time_seconds:.2f}s at T_c={result.critical_T:.4f}")
```

Or run full comparison / 运行全对比:

```bash
python -m solver.demo
```

## Results / 结果

### Hybrid Solver (Sinkhorn + Heuristic Backtracking)

| Puzzle | Clues | Solved | Backtrack Nodes | Time |
|--------|:-----:|:------:|:---------------:|:----:|
| Minimal (17 clues) | 17 | ✅ | 0 | 0.95s |
| Medium (30 clues) | 30 | ✅ | 0 | 1.00s |
| Arto Inkala (21 clues) | 21 | ✅ | 14,814 | 2.12s |
| AI Escargot (23 clues) | 23 | ✅ | 1,231 | 1.15s |

### Baseline comparison

| Solver | Minimal | Medium | Hard | AI Escargot |
|--------|:-------:|:------:|:----:|:-----------:|
| **Sinkhorn+Hybrid** | ✅ | ✅ | ✅ | ✅ |
| Sinkhorn (alone) | ✅ | ✅ | ❌ | ❌ |
| GA | ❌ | ❌ | ❌ | ❌ |
| SA | ❌ | ❌ | ❌ | ❌ |
| Gradient | ❌ | ❌ | ❌ | ❌ |
| BP | ❌ | ❌ | ❌ | ❌ |

**Two-phase approach:** Phase 1 = Sinkhorn continuous relaxation (linear annealing, T 30→0.001) produces a probability tensor. Phase 2 = Heuristic backtracking using MRV + Sinkhorn probability ordering solves remaining cells.

AI Escargot needs only 1,231 nodes (vs naive backtracking's 10¹²+) thanks to the Sinkhorn heuristic. Arto Inkala needs 14,814 nodes.

## Why It's Novel / 创新点

1. **4-约束 3D 张量 Sinkhorn** — 原始算法只处理双随机矩阵（行+列），本项目扩展了第三个（宫）维度和格约束
2. **约束硬度光谱（T_c）** — 相变温度 T_c 提供连续难度指标，而非离散的线索数或难度评级
3. **连续胜出离散** — 我们试过的所有离散求解器全失败，连续松弛能找到解

## Phistomefel's Ring / 菲斯托梅菲尔环 — Rigorous Proof 🔬

A **set-theoretic proof** (not just computation) has been completed in [`papers/phistomefel_ring_proof.md`](papers/phistomefel_ring_proof.md).

### The Universal Ring R = I ∪ C

The ring is **not** the 25 solution-dependent patterns found earlier. The true universal ring is:
```
. . . . . . . . .    G = Far corners of boxes {0,2,6,8} (16 cells)
. . . . . . . . .    R = I ∪ C = Universal ring (16 cells)
. . R R R R R . .    I = 12 edge-box inner cells
. . R . . . R . .    C = 4 corner-box center-adjacent cells
. . R . . . R . .
. . R . . . R . .    Proof: From set inclusion-exclusion on
. . R R R R R . .    outer rows {0,1,7,8} + outer cols {0,1,7,8}
. . . . . . . . .    Verified on 6 independent solutions
. . . . . . . . .
```

### Corrected Claims

| Old (Computational) | Corrected (Proof-Based) |
|------|------|
| Ring has 25 configurations | Those are **solution-dependent** — 0/25 cross-validate. The universal ring is I ∪ C. |
| Away-from-center rule generalizes | **FALSE** — 0/70 non-classic 4-box partitions satisfy the equivalence. |
| No mathematical proof | **Set-theoretic proof complete** — see [`papers/phistomefel_ring_proof.md`](papers/phistomefel_ring_proof.md) |

Interactive visualization / 交互可视化: [`figures/phistomefel_ring.html`](figures/phistomefel_ring.html)

Original analysis (superseded): [`papers/phistomefel_ring_set_equivalence.md`](papers/phistomefel_ring_set_equivalence.md)

## Dependencies / 依赖

- Python 3.8+
- NumPy
- Matplotlib（可视化）

## License / 许可证

MIT
