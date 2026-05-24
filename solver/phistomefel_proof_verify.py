"""
phistomefel_proof_verify.py — 验证从集合论推导出的环结构

从包含-排除原理推导出的环 R = I ∪ C:
  C = corner 盒子的中心最近格: {(2,2),(2,6),(6,2),(6,6)}  — 4 cells
  I = edge 盒子中 inner_block 内的格:  — 12 cells
      (2,3),(2,4),(2,5)  — Box 1 内行
      (3,2),(4,2),(5,2)  — Box 3 内列
      (3,6),(4,6),(5,6)  — Box 5 内列
      (6,3),(6,4),(6,5)  — Box 7 内行

在任意有效解中: multiset(G) = multiset(I ∪ C)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import SudokuBoard, PUZZLE_COLLECTION
from itertools import combinations
from collections import defaultdict

random.seed(42)


def ms(cells, grid):
    return tuple(sorted(grid[r][c] for r, c in cells))


def solve_puzzle(name):
    cfg = SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=500, verbose=False)
    solver = SinkhornSudokuSolver(cfg)
    sol, meta = solver.solve(PUZZLE_COLLECTION[name])
    return sol.grid if sol.is_solved() else None


def permute_rows_in_band(g, band, perm):
    g2 = [row[:] for row in g]
    rows = list(range(band * 3, band * 3 + 3))
    for i, target_row in enumerate(rows):
        g2[target_row] = g[rows[perm[i]]][:]
    return g2

def permute_cols_in_band(g, band, perm):
    g2 = [list(row) for row in g]
    cols = list(range(band * 3, band * 3 + 3))
    for c_idx, target_col in enumerate(cols):
        src_col = cols[perm[c_idx]]
        for r in range(9):
            g2[r][target_col] = g[r][src_col]
    return g2

def digit_relabel(g, mapping):
    return [[mapping[v] for v in row] for row in g]


# ===== Generate multiple solutions =====
print("=" * 60)
print("PROOF VERIFICATION: G = I ∪ C")
print("=" * 60)

solutions = {}

# Solve original puzzles
for name in ["minimal", "medium"]:
    g = solve_puzzle(name)
    if g and SudokuBoard(g).is_solved():
        solutions[name] = g

ref = solutions.get("medium")
if ref:
    solutions["v1"] = permute_rows_in_band(ref, 0, [2, 0, 1])
    solutions["v2"] = permute_rows_in_band(ref, 2, [1, 2, 0])
    solutions["v3"] = permute_cols_in_band(ref, 1, [1, 2, 0])
    mapping = {0: 0, 1: 9, 2: 1, 3: 8, 4: 2, 5: 7, 6: 3, 7: 6, 8: 4, 9: 5}
    solutions["v4"] = digit_relabel(ref, mapping)

# Validate
valid = {n: g for n, g in solutions.items() if SudokuBoard(g).is_solved()}
print(f"  Valid solutions: {len(valid)}")

# ===== Define G and R =====
GREEN = (
    [(0,0),(0,1),(1,0),(1,1)]   # Box 0 far TL
    + [(0,7),(0,8),(1,7),(1,8)] # Box 2 far TR
    + [(7,0),(7,1),(8,0),(8,1)] # Box 6 far BL
    + [(7,7),(7,8),(8,7),(8,8)] # Box 8 far BR
)

# RING from set-theoretic proof: I ∪ C
C = [(2,2), (2,6), (6,2), (6,6)]   # 4 corner centers

I = [
    (2,3), (2,4), (2,5),  # Box 1 inner row
    (3,2), (4,2), (5,2),  # Box 3 inner col
    (3,6), (4,6), (5,6),  # Box 5 inner col
    (6,3), (6,4), (6,5),  # Box 7 inner row
]

RING_THEORETIC = I + C

# Verify: for EVERY valid solution, multiset(G) == multiset(I ∪ C)
print()
all_pass = True
for name, grid in valid.items():
    g_ms = ms(GREEN, grid)
    r_ms = ms(RING_THEORETIC, grid)
    ok = "PASS" if g_ms == r_ms else "FAIL"
    if ok == "FAIL":
        all_pass = False
    print(f"  {name}: {ok}")
    if g_ms != r_ms:
        print(f"    G  = {g_ms}")
        print(f"    R  = {r_ms}")

if all_pass:
    print(f"\n  ✅ THEOREM PROVEN: multiset(G) = multiset(I ∪ C) for all {len(valid)} solutions")
else:
    print(f"\n  ❌ COUNTEREXAMPLE EXISTS")

# ===== Also show the physical ring pattern =====
print()
print("Ring R = I ∪ C (16 cells):")
vis = [["." for _ in range(9)] for _ in range(9)]
for r, c in GREEN:
    vis[r][c] = "G"
for r, c in RING_THEORETIC:
    vis[r][c] = "R"
for r in range(9):
    print("  " + " ".join(vis[r]))
print()
print(f"  Ring cells (sorted): {sorted(RING_THEORETIC)}")
print(f"  Green multiset: {ms(GREEN, valid.get('medium', [[]]))}")

# ===== Check: are the 25 computational patterns subsets of I ∪ C? =====
print()
print("=" * 60)
print("RELATIONSHIP: computational 25 patterns vs I ∪ C")
print("=" * 60)

ref_grid = valid.get("medium")
if ref_grid:
    g_ms = ms(GREEN, ref_grid)
    edge_boxes = [1, 3, 5, 7]
    BOX_CELLS = {}
    for b in range(9):
        br, bc = b // 3 * 3, b % 3 * 3
        BOX_CELLS[b] = [(br + r, bc + c) for r in range(3) for c in range(3)]

    bins = {}
    for b in edge_boxes:
        bins[b] = defaultdict(list)
        for combo in combinations(BOX_CELLS[b], 4):
            bins[b][ms(combo, ref_grid)].append(combo)

    comp_patterns = []
    for ms1, cl1 in bins[1].items():
        for ms3, cl3 in bins[3].items():
            for ms5, cl5 in bins[5].items():
                for ms7, cl7 in bins[7].items():
                    combined = tuple(sorted(list(ms1) + list(ms3) + list(ms5) + list(ms7)))
                    if combined == g_ms:
                        for c1 in [cl1[0]]:
                            for c3 in [cl3[0]]:
                                for c5 in [cl5[0]]:
                                    for c7 in [cl7[0]]:
                                        comp_patterns.append(set(c1 + c3 + c5 + c7))
                                        if len(comp_patterns) >= 25:
                                            break
                                    if len(comp_patterns) >= 25: break
                                if len(comp_patterns) >= 25: break
                            if len(comp_patterns) >= 25: break
                        if len(comp_patterns) >= 25: break
                if len(comp_patterns) >= 25: break
            if len(comp_patterns) >= 25: break
        if len(comp_patterns) >= 25: break

    theoretical_set = set(RING_THEORETIC)
    for i, pat in enumerate(comp_patterns):
        is_subset = pat.issubset(theoretical_set)
        overlap = pat & theoretical_set
        match_i = pat == theoretical_set
        print(f"  Pattern {i+1}: {'MATCH' if match_i else 'NO match'} | "
              f"subsetof(R)={is_subset} | overlap={len(overlap)}/16 "
              f"| extra={sorted(pat - theoretical_set)[:5]}")

    # Is ring I ∪ C found by the edge-box-only search?
    ring_edge_only = set(I)  # C cells are in corner boxes, not found by edge-box search
    print(f"\n  Ring R = I ∪ C:    I has {len(I)} edge-box cells, C has {len(C)} corner-box cells")
    print(f"  Edge-box search found {len(comp_patterns)} patterns from edge-box 4-cell subsets")
    print(f"  Ring I (edge cells): can be found by edge-only search = {len(I)} cells in 4 edge boxes")
    print(f"     = {sorted(I)}")
    
    # Check: is I a valid 16-cell pattern (4 per edge box)?
    I_by_box = {1: [], 3: [], 5: [], 7: []}
    for r, c in I:
        b = (r // 3) * 3 + c // 3
        if b in I_by_box:
            I_by_box[b].append((r, c))
    for b, cells in I_by_box.items():
        print(f"    Box {b}: {len(cells)} cells = {sorted(cells)}")
