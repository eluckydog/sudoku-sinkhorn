"""phistomefel_analysis.py - Phistomefel Ring verification & pattern search"""

import sys
from itertools import combinations
sys.path.insert(0, '.')
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import PUZZLE_COLLECTION


def solver_solve(board):
    solver = SinkhornSudokuSolver(
        SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=400, verbose=False)
    )
    result = solver.solve(board)
    if isinstance(result, tuple) and len(result) >= 1:
        sboard = result[0]
        if hasattr(sboard, 'is_solved') and sboard.is_solved():
            return sboard.grid
    return None


def multiset(cells, grid):
    return tuple(sorted(grid[r][c] for r, c in cells))


# ===== Box helpers =====
def box_2x2_abs(box_idx, corner):
    """Return 4 cells of a 2x2 corner of a 3x3 box.
    corner: 0=TL, 1=TR, 2=BL, 3=BR"""
    br = (box_idx // 3) * 3
    bc = (box_idx % 3) * 3
    offsets = [
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,1),(0,2),(1,1),(1,2)],
        [(1,0),(1,1),(2,0),(2,1)],
        [(1,1),(1,2),(2,1),(2,2)],
    ]
    return [(br + r, bc + c) for (r, c) in offsets[corner]]


def box_corner_cells(box_idx):
    """Return 4 corner cells of a 3x3 box (not a 2x2 block)"""
    br = (box_idx // 3) * 3
    bc = (box_idx % 3) * 3
    return [(br, bc), (br, bc + 2), (br + 2, bc), (br + 2, bc + 2)]


# ===== Phistomefel Ring candidates =====

# Green = 2x2 corners AWAY from center in boxes 0,2,6,8
GREEN = (
    box_2x2_abs(0, 0) + box_2x2_abs(2, 1) +
    box_2x2_abs(6, 2) + box_2x2_abs(8, 3)
)

# Ring candidate A: 4 corner cells of each edge box 1,3,5,7
RING_A = (
    box_corner_cells(1) + box_corner_cells(3) +
    box_corner_cells(5) + box_corner_cells(7)
)

# Ring candidate B: 2x2 corners of edge boxes TOWARD center
RING_B = (
    box_2x2_abs(1, 3) + box_2x2_abs(3, 2) +
    box_2x2_abs(5, 3) + box_2x2_abs(7, 1)
)

# Ring candidate C: 2x2 blocks in edge boxes (the inward-facing 2x2s)
RING_C = (
    box_2x2_abs(1, 2) + box_2x2_abs(3, 1) +
    box_2x2_abs(5, 2) + box_2x2_abs(7, 0)
)

# ===== Solve & verify =====
print("Soving medium puzzle (Sinkhorn)...")
grid = solver_solve(PUZZLE_COLLECTION["medium"])

if grid is None:
    print("Failed to solve!")
    sys.exit(1)

print("Solved grid:")
for r in range(9):
    print(f"  {[grid[r][c] for c in range(9)]}")
print()

# Get green multiset
g_ms = multiset(GREEN, grid)

ring_candidates = [
    ("Ring-4corner of edge boxes", RING_A),
    ("Ring-2x2 inward edge", RING_C),
    ("Ring-2x2 corner edge", RING_B),
    ("Ring-2x2 TL of edge", 
     box_2x2_abs(1,0)+box_2x2_abs(3,0)+box_2x2_abs(5,1)+box_2x2_abs(7,2)),
    ("Ring-2x2 TR of edge",
     box_2x2_abs(1,1)+box_2x2_abs(3,1)+box_2x2_abs(5,0)+box_2x2_abs(7,3)),
]

print(f"Green (2x2 corners of boxes 0,2,6,8): {g_ms}")
print()

for label, cells in ring_candidates:
    r_ms = multiset(cells, grid)
    ok = "OK" if r_ms == g_ms else "X"
    print(f"  {ok} {label}: {r_ms}")

# Fall back: systematic search of all 16-cell subsets from edge boxes
print()
print("Systematic search: all 16-cell subsets of boxes 1,3,5,7 that match green...")

edge_boxes_cells = []
for b in [1, 3, 5, 7]:
    br = (b // 3) * 3
    bc = (b % 3) * 3
    for r in range(3):
        for c in range(3):
            edge_boxes_cells.append((br + r, bc + c))

# Each edge box has 9 cells. We need 4 cells from each = 16 total.
# For each edge box, try all 4-cell subsets and find matching combinations
from itertools import combinations, product

box1_cells = [(r, c) for r in range(3) for c in range(3, 6)]   # 9 cells
box3_cells = [(r, c) for r in range(3, 6) for c in range(3)]   # 9 cells
box5_cells = [(r, c) for r in range(3, 6) for c in range(6, 9)]  # 9 cells
box7_cells = [(r, c) for r in range(6, 9) for c in range(3, 6)]  # 9 cells

# Generate all 4-cell subsets of each edge box (C(9,4) = 126 each)
subs1 = list(combinations(box1_cells, 4))
subs3 = list(combinations(box3_cells, 4))
subs5 = list(combinations(box5_cells, 4))
subs7 = list(combinations(box7_cells, 4))

print(f"  Box 1 subsets: {len(subs1)}")
print(f"  Box 3 subsets: {len(subs3)}")
print(f"  Box 5 subsets: {len(subs5)}")
print(f"  Box 7 subsets: {len(subs7)}")
print(f"  Total combinations: {len(subs1)*len(subs3)*len(subs5)*len(subs7)}")

# Reduce by binning: store subsets by their multiset, deduplicate
def cells_to_ms(cells):
    return tuple(sorted(grid[r][c] for r, c in cells))

from collections import defaultdict

bins1 = defaultdict(list)
for s in subs1:
    ms = cells_to_ms(s)
    bins1[ms].append(s)

bins3 = defaultdict(list)
for s in subs3:
    ms = cells_to_ms(s)
    bins3[ms].append(s)

bins5 = defaultdict(list)
for s in subs5:
    ms = cells_to_ms(s)
    bins5[ms].append(s)

bins7 = defaultdict(list)
for s in subs7:
    ms = cells_to_ms(s)
    bins7[ms].append(s)

print(f"  Unique multisets: Box1={len(bins1)}, Box3={len(bins3)}, Box5={len(bins5)}, Box7={len(bins7)}")

# Now find: which 4-cell multiset from each box adds up to the green multiset?
found_rings = []
for ms1, cells1_list in bins1.items():
    for ms3, cells3_list in bins3.items():
        for ms5, cells5_list in bins5.items():
            for ms7, cells7_list in bins7.items():
                combined = tuple(sorted(list(ms1) + list(ms3) + list(ms5) + list(ms7)))
                if combined == g_ms:
                    for c1 in cells1_list:
                        for c3 in cells3_list:
                            for c5 in cells5_list:
                                for c7 in cells7_list:
                                    found_rings.append(c1 + c3 + c5 + c7)
                                    if len(found_rings) >= 5:
                                        break
                                if len(found_rings) >= 5: break
                            if len(found_rings) >= 5: break
                        if len(found_rings) >= 5: break
                    if len(found_rings) >= 5: break
            if len(found_rings) >= 5: break
        if len(found_rings) >= 5: break

print(f"  Matching ring configurations found: {len(found_rings)}")
for i, ring in enumerate(found_rings[:5]):
    ring_sorted = sorted(ring)
    print(f"  Ring {i+1}: {ring_sorted}")
    print(f"          values: {multiset(ring, grid)}")
