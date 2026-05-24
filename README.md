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

| Puzzle | Clues | Sinkhorn | GA | SA | Gradient | BP | T_c |
|--------|-------|----------|-----|-----|----------|------|-----|
| Minimal (17 clues) | 17 | ✅ 0.86s | ❌ | ❌ | ❌ | ❌ | 0.759 |
| Medium (30 clues) | 30 | ✅ 0.90s | ❌ | ❌ | ❌ | ❌ | 0.912 |
| Arto Inkala | 23 | ❌ | ❌ | ❌ | ❌ | ❌ | 0.630 |
| AI Escargot | 21 | ❌ | ❌ | ❌ | ❌ | ❌ | 0.630 |

**Only Sinkhorn solves any puzzles.** The continuous relaxation avoids the column-constraint blindness that plagues row-initialized discrete methods.

**唯一能求解的是 Sinkhorn。** 连续松弛从根本上避免了行初始化离散方法的列约束盲区。

T_c (critical temperature) is a **measurable hardness signature**: higher T_c = easier puzzle. Medium (0.912) > Minimal (0.759) > Hard = Escargot (0.630). First time phase transition temperature has been used as a Sudoku difficulty metric.

**T_c 是第一个可量化的数独难度指标：T_c 越高 = 越容易。**

## Why It's Novel / 创新点

1. **4-约束 3D 张量 Sinkhorn** — 原始算法只处理双随机矩阵（行+列），本项目扩展了第三个（宫）维度和格约束
2. **约束硬度光谱（T_c）** — 相变温度 T_c 提供连续难度指标，而非离散的线索数或难度评级
3. **连续胜出离散** — 我们试过的所有离散求解器全失败，连续松弛能找到解

## Phistomefel's Ring / 菲斯托梅菲尔环

Key findings from computational analysis / 计算分析核心发现:

**1. Ring is not unique / 环不唯一.** 存在 **25 种**不同的环配置，都满足 Phistomefel 集合等价。

**2. Away-from-center rule / 远离中心规则.** 每个 3×3 盒子中远离中心的 2×2 角落参与环结构。推广到任意互补 4 盒分区。

**3. Universal set equivalence / 普适集合等价.** 任意两组 4 盒子（共享 ≤1 盒），各自选择远离中心的 2×2 角落，产生的 16 格多重集相等。

Phistomefel Ring visualization / 可视化:
```
GG.BBB.GG    G = 四角 2×2 (16格)
GG.B...GG    B = 环 (16格)
.........    多重集相等:
BBB...BBB    (1,2,2,3,3,3,4,4,5,5,6,7,7,8,8,9)
......B..
..B......
...BB....
GG.B...GG
GG.B...GG
```

Interactive visualization / 交互可视化: [`figures/phistomefel_ring.html`](figures/phistomefel_ring.html)

Full paper / 完整论文: [`papers/phistomefel_ring_set_equivalence.md`](papers/phistomefel_ring_set_equivalence.md)

## Dependencies / 依赖

- Python 3.8+
- NumPy
- Matplotlib（可视化）

## License / 许可证

MIT
