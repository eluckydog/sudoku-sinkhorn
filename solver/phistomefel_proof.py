"""
phistomefel_proof.py — Phistomefel Ring mathematical proof + generalization test

Two purposes:
1. Generate multiple valid solutions to test if the ring is solution-dependent
2. Verify/falsify the generalization conjecture for other 4-box partitions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import random
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import SudokuBoard, PUZZLE_COLLECTION

random.seed(42)


# ====== Helper functions ======

def ms(cells, grid):
    """Get sorted multiset of digits from a set of cells"""
    return tuple(sorted(grid[r][c] for r, c in cells))


def solve_puzzle(name):
    """Solve a puzzle and return the grid"""
    cfg = SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=500, verbose=False)
    solver = SinkhornSudokuSolver(cfg)
    sol, meta = solver.solve(PUZZLE_COLLECTION[name])
    return sol.grid if sol.is_solved() else None


# ====== Generate multiple independent valid solutions ======

print("=" * 65)
print("GENERATING MULTIPLE VALID SOLUTIONS")
print("=" * 65)

solutions = {}

# 1. Solve different puzzles
for name in ["minimal", "medium"]:
    g = solve_puzzle(name)
    if g:
        solutions[name] = g
        print(f"  Solved {name}: valid={SudokuBoard(g).is_valid()}")

# 2. Generate solution variants via legal Sudoku transformations
ref = solutions.get("medium")
if ref:
    def permute_rows_in_band(g, band, perm):
        g2 = [row[:] for row in g]
        rows = list(range(band * 3, band * 3 + 3))
        for i, target_row in enumerate(rows):
            g2[target_row] = g[rows[perm[i]]][:]
        return g2

    def permute_cols_in_band(g, band, perm):
        g2 = [row[:] for row in g]
        cols = list(range(band * 3, band * 3 + 3))
        for c in range(9):
            for r in range(9):
                g2[r][c] = g[r][c]  # copy
        for c_idx, target_col in enumerate(cols):
            src_col = cols[perm[c_idx]]
            for r in range(9):
                g2[r][target_col] = g[r][src_col]
        return g2

    def permute_bands(g, axis, perm):
        """Permute whole 3-row/3-col bands (axis=0 for rows, 1 for cols)"""
        if axis == 0:
            g2 = [[0]*9 for _ in range(9)]
            for i in range(3):
                for r in range(3):
                    g2[perm[i]*3 + r] = g[i*3 + r]
            return g2
        else:
            g2 = [row[:] for row in g]
            cols_copy = [None] * 9
            for i in range(3):
                for c in range(3):
                    src = i*3 + c
                    dst = perm[i]*3 + c
                    cols_copy[dst] = [g[r][src] for r in range(9)]
            for c in range(9):
                for r in range(9):
                    g2[r][c] = cols_copy[c][r]
            return g2

    def digit_relabel(g, mapping):
        """Relabel digits 1-9 using a permutation"""
        g2 = [row[:] for row in g]
        for r in range(9):
            for c in range(9):
                g2[r][c] = mapping[g[r][c]]
        return g2

    # Variant 1: permute rows within top band
    g1 = permute_rows_in_band(ref, 0, [2, 0, 1])
    solutions["row_perm_top"] = g1

    # Variant 2: permute rows within bottom band
    g2 = permute_rows_in_band(ref, 2, [1, 2, 0])
    solutions["row_perm_bot"] = g2

    # Variant 3: permute cols within middle band
    g3 = permute_cols_in_band(ref, 1, [1, 2, 0])
    solutions["col_perm_mid"] = g3

    # Variant 4: swap full bands
    g4 = permute_bands(ref, 0, [2, 0, 1])
    solutions["band_swap"] = g4

    # Variant 5: digit relabel
    mapping = {0: 0, 1: 9, 2: 1, 3: 8, 4: 2, 5: 7, 6: 3, 7: 6, 8: 4, 9: 5}
    g5 = digit_relabel(ref, mapping)
    solutions["digit_relabel"] = g5

# 3. Validate all solutions
valid_solutions = {}
for name, g in solutions.items():
    b = SudokuBoard(g)
    if b.is_solved():
        valid_solutions[name] = g
        print(f"  {name}: SOLVED (valid)")
    else:
        print(f"  {name}: INVALID - {b.count_empty()} empty")

print(f"\nTotal valid solutions: {len(valid_solutions)}")


# ====== PART 1: Is the ring solution-dependent or fixed? ======

print("\n" + "=" * 65)
print("PART 1: FIXED vs SOLUTION-DEPENDENT RING")
print("=" * 65)

# Green = 2x2 far corners of boxes 0,2,6,8
GREEN = (
    [(0, 0), (0, 1), (1, 0), (1, 1)]   # Box 0 TL corner
    + [(0, 7), (0, 8), (1, 7), (1, 8)]  # Box 2 TR corner
    + [(7, 0), (7, 1), (8, 0), (8, 1)]  # Box 6 BL corner
    + [(7, 7), (7, 8), (8, 7), (8, 8)]  # Box 8 BR corner
)

# Edge box definitions
BOX_CELLS = {}
for b in range(9):
    br, bc = b // 3 * 3, b % 3 * 3
    BOX_CELLS[b] = [(br + r, bc + c) for r in range(3) for c in range(3)]

EDGE_BOXES = [1, 3, 5, 7]

# Test: for each solution, find all 16-cell subsets of edge boxes that match G
from itertools import combinations
from collections import defaultdict

# For one representative solution (medium), find all matching ring patterns
print("\nFinding all ring patterns for 'medium' solution...")
ref_grid = valid_solutions.get("medium")
if ref_grid:
    g_ms = ms(GREEN, ref_grid)
    print(f"  Green multiset: {g_ms}")

    # Build multiset bins for each edge box
    def cells_to_ms(cells):
        return tuple(sorted(ref_grid[r][c] for r, c in cells))

    bins = {}
    for b in EDGE_BOXES:
        bins[b] = defaultdict(list)
        for combo in combinations(BOX_CELLS[b], 4):
            bins[b][cells_to_ms(combo)].append(combo)

    # Find matching combinations
    patterns_by_solution = {}
    candidates = []
    for ms1, cl1 in bins[1].items():
        for ms3, cl3 in bins[3].items():
            for ms5, cl5 in bins[5].items():
                for ms7, cl7 in bins[7].items():
                    combined = tuple(sorted(list(ms1) + list(ms3) + list(ms5) + list(ms7)))
                    if combined == g_ms:
                        # Store one representative per unique combo
                        for c1 in [cl1[0]]:
                            for c3 in [cl3[0]]:
                                for c5 in [cl5[0]]:
                                    for c7 in [cl7[0]]:
                                        candidates.append(tuple(c1 + c3 + c5 + c7))
                                        if len(candidates) >= 25:
                                            break
                                    if len(candidates) >= 25: break
                                if len(candidates) >= 25: break
                            if len(candidates) >= 25: break
                        if len(candidates) >= 25: break
                if len(candidates) >= 25: break
            if len(candidates) >= 25: break
        if len(candidates) >= 25: break

    print(f"  Found {len(candidates)} candidate ring patterns for 'medium'")
    patterns_by_solution["medium"] = candidates

    # Now test each candidate on ALL other solutions
    print("\nCross-validation: testing each candidate ring on all solutions...")
    universal_patterns = list(candidates)  # start with all
    for sol_name, sol_grid in valid_solutions.items():
        if sol_name == "medium":
            continue
        sol_g_ms = ms(GREEN, sol_grid)
        still_valid = []
        for ridx, ring_cells in enumerate(universal_patterns):
            if ms(ring_cells, sol_grid) == sol_g_ms:
                still_valid.append(ring_cells)
        universal_patterns = still_valid
        print(f"  After '{sol_name}': {len(universal_patterns)} patterns remain")

    if universal_patterns:
        print(f"\n  ✅ UNIVERSAL PATTERNS FOUND: {len(universal_patterns)}")
        for i, ring in enumerate(universal_patterns[:3]):
            print(f"  Pattern {i+1}:")
            # Show per-box
            def box_of(cell):
                r, c = cell
                return (r // 3) * 3 + c // 3
            for b in EDGE_BOXES:
                cells = sorted([c for c in ring if box_of(c) == b])
                print(f"    Box {b}: {cells}")
    else:
        print(f"\n  ❌ NO universal patterns — ring IS solution-dependent")


# ====== PART 2: Generalization conjecture ======
# Test other complementary 4-box partitions

print("\n" + "=" * 65)
print("PART 2: GENERALIZATION CONJECTURE")
print("=" * 65)
print("  Claim: ANY complementary 4-box partition, selecting")
print("  away-from-center 2x2 corners, produces equal 16-cell multisets.")
print()

ref_grid = valid_solutions.get("medium")
if ref_grid:
    # Define the "away-from-center" 2x2 corner for any box
    def away_2x2(box_idx):
        """Return the 4 cells of the 2x2 corner AWAY from center box (4)"""
        br, bc = box_idx // 3 * 3, box_idx % 3 * 3
        # Center box center at (4,4) ... boxes are at band positions
        box_br, box_bc = box_idx // 3, box_idx % 3  # 0,1,2
        center_br, center_bc = 1, 1  # box 4 is at band (1,1)
        dr = box_br - center_br  # -1, 0, or 1
        dc = box_bc - center_bc  # -1, 0, or 1
        # 'Away' means the corner opposite to the center direction
        if dr == -1:
            r_off = 0  # above center -> use bottom rows of box
        elif dr == 1:
            r_off = 1  # below center -> use top rows
        else:
            r_off = 0  # same band -> ambiguous, try both
        if dc == -1:
            c_off = 0
        elif dc == 1:
            c_off = 1
        else:
            c_off = 0

        # The 2x2 corner away from center
        away_corners = {
            # (dr, dc): (r_offset, c_offset, r_alt, c_alt)
            # r_offset 0=top half(0,1), 1=bottom half(1,2)
            # c_offset 0=left half(0,1), 1=right half(1,2)
            (-1, -1): (0, 0),  # above+left of center -> TL of box is away... no!
            # Actually, if box is ABOVE center, the BOTTOM of the box is away
            # If box is LEFT of center, the RIGHT of the box is away
        }

        # Away-from-center means the OPPOSITE corner from center
        # Box above center (box_br=0): away = bottom = rows 1,2 of box
        # Box below center (box_br=2): away = top = rows 0,1 of box
        # Box left of center (box_bc=0): away = right = cols 1,2 of box
        # Box right of center (box_bc=2): away = left = cols 0,1 of box

        r_start = 0
        c_start = 0
        if box_br < center_br:
            r_start = 1  # above center: far = bottom half
        elif box_br > center_br:
            r_start = 0  # below center: far = top half
        else:
            r_start = 0  # same band - need special handling for center box

        if box_bc < center_bc:
            c_start = 1  # left of center: far = right half
        elif box_bc > center_bc:
            c_start = 0  # right of center: far = left half
        else:
            c_start = 0

        return [(br + r_start + dr, bc + c_start + dc)
                for dr in range(2) for dc in range(2)]

    # Test the classic partition: corners {0,2,6,8} vs edge boxes {1,3,5,7}
    print("Test 1: Classic partition (boxes {0,2,6,8} vs {1,3,5,7})")
    green_set = []
    for b in [0, 2, 6, 8]:
        green_set.extend(away_2x2(b))
    g_ms = ms(green_set, ref_grid)
    print(f"  Green set (away corners of boxes 0,2,6,8):  {g_ms}")

    ring_set = []
    for b in [1, 3, 5, 7]:
        ring_set.extend(away_2x2(b))
    r_ms = ms(ring_set, ref_grid)
    ok = "PASS" if r_ms == g_ms else "FAIL"
    print(f"  Ring set (away corners of boxes 1,3,5,7): {r_ms} — {ok}")

    # The away_2x2 for edge boxes gives the INWARD-facing 2x2 corners
    # (toward center), NOT the ring! Let me check this.
    # Box 1 (above center): away=r_start=1 → bottom rows 1,2
    #   left of center (col_band 1 = same as center): c_start=0
    #   So Box 1 away = (1,0),(1,1),(2,0),(2,1) in box coords
    #   = absolute: (1,4),(1,5),(2,4),(2,5) or (1,3),(1,4),(2,3),(2,4)?
    # Wait, box 1 top-left = (0,3). So box-local (0,0)=(0,3), (0,1)=(0,4), etc.
    # away cells in box 1: r_start=1, c_start=0 → local (1,0),(1,1),(2,0),(2,1)
    # = absolute: (1,3),(1,4),(2,3),(2,4)
    print(f"  Away corners of box 1: {away_2x2(1)}")
    print(f"  Away corners of box 3: {away_2x2(3)}")
    print(f"  Away corners of box 5: {away_2x2(5)}")
    print(f"  Away corners of box 7: {away_2x2(7)}")
    print(f"  VALUES: {r_ms}")

    # Now try OTHER partitions
    # Test 2: Left column of boxes {0,3,6} vs right column {2,5,8}
    # But we need 4-box complementary groups. The classic is 4+4+1.
    # Any partition of 9 boxes into 4+4+1, where the center is the +1

    # All possible 4-box subsets that avoid the center (box 4)
    all_boxes = list(range(9))
    all_boxes.remove(4)  # center box exluded

    # Test ALL complementary 4-box pairs
    print("\nTest 2: All complementary 4-box partitions (excluding center)")
    from itertools import combinations

    pass_count = 0
    fail_count = 0
    for combo in combinations(all_boxes, 4):
        comp = tuple(sorted(set(all_boxes) - set(combo)))
        if len(comp) != 4:
            continue
        set1 = []
        set2 = []
        for b in combo:
            set1.extend(away_2x2(b))
        for b in comp:
            set2.extend(away_2x2(b))
        ms1 = ms(set1, ref_grid)
        ms2 = ms(set2, ref_grid)
        if ms1 == ms2:
            pass_count += 1
            print(f"  ✅ {sorted(combo)} vs {comp}: PASS")
        else:
            fail_count += 1
            print(f"  ❌ {sorted(combo)} vs {comp}: FAIL")
            print(f"      set1={ms1}")
            print(f"      set2={ms2}")

    print(f"\n  Summary: {pass_count} passed, {fail_count} failed")
    if fail_count == 0:
        print("  ✅ Generalization CONFIRMED for all 4-box partitions")
    else:
        print("  ❌ Generalization REFUTED — counterexamples exist")
