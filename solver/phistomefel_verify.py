"""
phistomefel_verify.py - Phistomefel Ring correct verification
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from solver.sinkhorn_solver import SinkhornSudokuSolver, SinkhornConfig
from solver.board import PUZZLE_COLLECTION

s = SinkhornSudokuSolver(SinkhornConfig(T_start=10.0, T_end=0.001, n_iter=400, verbose=False))
r = s.solve(PUZZLE_COLLECTION['medium'])
g = r[0].grid


def ms(cells):
    return tuple(sorted(g[r][c] for r, c in cells))


def show_grid():
    for row in g:
        print("      " + " ".join(str(v) for v in row))


def show_ring(name, green, blue):
    vis = [["." for _ in range(9)] for _ in range(9)]
    for r, c in green:
        vis[r][c] = "G"
    for r, c in blue:
        vis[r][c] = "B"
    gms = ms(green)
    bms = ms(blue)
    eq = gms == bms
    print(f"  {name}: {'PASS' if eq else 'FAIL'}")
    print(f"    Green: {gms}")
    print(f"    Blue:  {bms}")
    for row in vis:
        print("    " + " ".join(row))
    print()


# === CORRECT Phistomefel Ring ===
# Green: 4 far 2x2 corners of boxes 0,2,6,8
GREEN = [
    (0, 0), (0, 1), (1, 0), (1, 1),  # Box 0 TL
    (0, 7), (0, 8), (1, 7), (1, 8),  # Box 2 TR
    (7, 0), (7, 1), (8, 0), (8, 1),  # Box 6 BL
    (7, 7), (7, 8), (8, 7), (8, 8),  # Box 8 BR
]

# The set-theoretic BLUE:
# Formed by (R[0:2] ∪ R[7:9]) ∩ C[3:6] + (R[3:6]) ∩ (C[0:2] ∪ C[6:9])
# i.e., the cross of the outer ring that isn't the corners
BLUE = [
    # Top band, center 3 cols
    (0, 3), (0, 4), (0, 5),
    # Bottom band, center 3 cols
    (8, 3), (8, 4), (8, 5),
    # Middle band, left 3 cols
    (3, 0), (3, 1), (3, 2),
    (4, 0), (4, 1), (4, 2),
    (5, 0), (5, 1), (5, 2),
    # Middle band, right 3 cols
    (3, 6), (3, 7), (3, 8),
    (4, 6), (4, 7), (4, 8),
    (5, 6), (5, 7), (5, 8),
]

# Actually that's 6 + 6 + 9 + 9 = 30 cells. Too many.
# The ring is only 16 cells, so most of these must be wrong.

# Let me try the ACTUAL set theory proof:
# Set A = (R1∪R9∪C1∪C9) \ (B1∪B3∪B7∪B9) ∪ (B5∩R1∩R9∩C1∩C9)
# No, this is getting circular.

# Let me look at the set proof from scratch:
# Corners = (R1∩C1) ∪ (R1∩C9) ∪ (R9∩C1) ∪ (R9∩C9) with R = {0,1}, C = {0,1} etc.
# That's: R[0:2] ∩ C[0:2] + R[0:2] ∩ C[7:9] + R[7:9] ∩ C[0:2] + R[7:9] ∩ C[7:9]

# The ring cells must be a FORMULA that uses row/col/box counting
# such that each digit appears the SAME number of times as in the corners.

# Each digit in corners:
# - In row 0: appears in cols {0,1,7,8} = 4 positions in row 0
# - In row 1: appears in cols {0,1,7,8} = 4 positions in row 1
# - In row 7: appears in cols {0,1,7,8} = 4 positions in row 7
# - In row 8: appears in cols {0,1,7,8} = 4 positions in row 8
# Total: 16 corner cells, 4 per row, 4 per column

# For the ring with 16 cells:
# Each digit should appear the same number of times.
# Since each digit appears 16/9 != integer in the corners,
# the ring is solution-dependent.

# The theorem is about EQUIVALENCE, not about counting per digit.
# It states: FOR ANY valid solution, multiset(corners) == multiset(ring).
# This is proven by set theory, not by counting.

# Let me use the actual formula:
# Far corners = rows {1,2,8,9} ∩ cols {1,2,8,9} [2x2 blocks]
# The remaining 4-corner pattern = rows {3,7} ∪ cols {3,7} - boxes {1,3,7,9} + box 5

# Wait - I think the correct formula is about the CENTER 4 rows/cols not the corners!

# From Cracking the Cryptic: 
# Far corners = the 16 cells formed by:
#   rows {1,9} × cols {1,9} (4 cells) = 4 corner cells of the GRID
#   + rows {1,9} × cols {2,8} (4 cells) = adjacent cells
#   + rows {2,8} × cols {1,9} (4 cells) = adjacent cells
#   + rows {2,8} × cols {2,8} (4 cells) = inner 2x2
# Wait that's just all 16 cells of the outer 4x4 = that's all cells in 
# rows {0,1,7,8} × cols {0,1,7,8} (4×4 = 16) which is ALL the outer ring cells!

# That can't be right because then the ring would be empty.

print("=" * 60)
print("PHISTOMEFEL RING")
print("=" * 60)
print()

print("Solved grid:")
show_grid()
print()

# Let me just verify what happens with the FAR corner definition
# vs the NEAR corner definition
green_far = [
    (0,0),(0,1),(1,0),(1,1),
    (0,7),(0,8),(1,7),(1,8),
    (7,0),(7,1),(8,0),(8,1),
    (7,7),(7,8),(8,7),(8,8),
]

green_near = [
    (1,1),(1,2),(2,1),(2,2),
    (1,6),(1,7),(2,6),(2,7),
    (6,1),(6,2),(7,1),(7,2),
    (6,6),(6,7),(7,6),(7,7),
]

show_ring("Far corners vs near corners", green_far, green_near)

# Test the 4-corner ring definition
ring_4corner = [
    (0,3),(0,5),(2,3),(2,5),  # Box 1
    (3,0),(3,2),(5,0),(5,2),  # Box 3
    (3,6),(3,8),(5,6),(5,8),  # Box 5
    (6,3),(6,5),(8,3),(8,5),  # Box 7
]
show_ring("Far corners vs 4-corner ring", green_far, ring_4corner)

# What about the OPPOSITE corners (inner 2x2 of corner boxes vs ring)?
show_ring("Near corners vs 4-corner ring", green_near, ring_4corner)

# The inner 2x2 of edge boxes
ring_2x2_inner = [
    (1,3),(1,4),(2,3),(2,4),  # Box 1 inner BR
    (3,1),(3,2),(4,1),(4,2),  # Box 3 inner BR
    (3,6),(3,7),(4,6),(4,7),  # Box 5 inner BL
    (6,3),(6,4),(7,3),(7,4),  # Box 7 inner TR
]
show_ring("Far corners vs inner 2x2 of edge", green_far, ring_2x2_inner)
show_ring("Near corners vs inner 2x2 of edge", green_near, ring_2x2_inner)

# Key finding: the Phistomefel Ring depends on the CORRECT pairing.
# From the set theory proof:
# The theorem only works when you pair the right two sets.
# Far corners (away from center) have a DIFFERENT multiset than near corners.
# The ring cells also have a different multiset.
# 
# The equivalence holds between SPECIFIC pairs:
#   Far corners ---???--- ring cells
# 
# From my earlier exhaustive search, I found 25 valid ring configurations
# from the edge boxes. Let me check the most symmetric one:

symmetric_ring = [
    (0,3),(0,4),(0,5),(1,3),   # Box 1: top 3 + one below
    (3,0),(3,1),(3,2),(5,2),   # Box 3: full left col + 1 cell
    (3,6),(3,7),(3,8),(4,6),   # Box 5: full right col + 1 cell  
    (6,3),(6,4),(7,3),(8,3),   # Box 7: top-left of box
]
show_ring("Far corners vs symmetric ring #1", green_far, symmetric_ring)
