"""Find the most symmetric Phistomefel ring patterns"""
import sys
sys.path.insert(0, '.')
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import PUZZLE_COLLECTION
from itertools import combinations
from collections import defaultdict

solver = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=400, verbose=False))
result = solver.solve(PUZZLE_COLLECTION['medium'])
grid = result[0].grid

# Edge box cells
edge_boxes = {}
for bi in [1, 3, 5, 7]:
    br = (bi // 3) * 3
    bc = (bi % 3) * 3
    edge_boxes[bi] = [(br + r, bc + c) for r in range(3) for c in range(3)]

def box2x2(bi, co):
    br = (bi // 3) * 3
    bc = (bi % 3) * 3
    off = [[(0,0),(0,1),(1,0),(1,1)],[(0,1),(0,2),(1,1),(1,2)],
           [(1,0),(1,1),(2,0),(2,1)],[(1,1),(1,2),(2,1),(2,2)]]
    return [(br+r, bc+c) for r, c in off[co]]

green = box2x2(0,0) + box2x2(2,1) + box2x2(6,2) + box2x2(8,3)

def ms(cells):
    return tuple(sorted(grid[r][c] for r, c in cells))

gms = ms(green)

print("Green corners:", gms)
print()

# Bin edge box subsets by multiset
boxes_data = {}
for bi in [1, 3, 5, 7]:
    bins = defaultdict(list)
    for combo in combinations(edge_boxes[bi], 4):
        bins[ms(combo)].append(combo)
    boxes_data[bi] = bins

# Find all matching combinations
found_patterns = []
for ms1, cl1 in boxes_data[1].items():
    for ms3, cl3 in boxes_data[3].items():
        for ms5, cl5 in boxes_data[5].items():
            for ms7, cl7 in boxes_data[7].items():
                combined = tuple(sorted(list(ms1) + list(ms3) + list(ms5) + list(ms7)))
                if combined == gms:
                    for c1 in cl1[:1]:
                        for c3 in cl3[:1]:
                            for c5 in cl5[:1]:
                                for c7 in cl7[:1]:
                                    ring = list(c1) + list(c3) + list(c5) + list(c7)
                                    # Build visualization
                                    vis = [["." for _ in range(9)] for _ in range(9)]
                                    for r, c in green: vis[r][c] = "G"
                                    for r, c in ring: vis[r][c] = "B"
                                    found_patterns.append((c1, c3, c5, c7, vis))
                                    if len(found_patterns) >= 10:
                                        break
                                if len(found_patterns) >= 10: break
                            if len(found_patterns) >= 10: break
                        if len(found_patterns) >= 10: break
                if len(found_patterns) >= 10: break
            if len(found_patterns) >= 10: break
        if len(found_patterns) >= 10: break
    if len(found_patterns) >= 10: break

print(f"Found {len(found_patterns)} patterns")
print()

for idx, (c1, c3, c5, c7, vis) in enumerate(found_patterns):
    print(f"Pattern {idx+1}:")
    print(f"  Box1: {sorted([(r,c) for r,c in c1])}")
    print(f"  Box3: {sorted([(r,c) for r,c in c3])}")
    print(f"  Box5: {sorted([(r,c) for r,c in c5])}")
    print(f"  Box7: {sorted([(r,c) for r,c in c7])}")
    print("  Grid:")
    for row in vis:
        print("    " + " ".join(row))
    print()
