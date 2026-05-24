"""
board.py - Sudoku board representation and constraint system

Core data structure: SudokuBoard (9x9)
Tensor view: 9x9x9 triples (row, col, value)
"""

import warnings
import numpy as np
from typing import List, Optional, Set

# Box coordinate mapping
BOX_MAP = {}
for b in range(9):
    br, bc = b // 3 * 3, b % 3 * 3
    cells = []
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            cells.append((r, c))
    BOX_MAP[b] = cells

CELL_TO_BOX = {}
for b, cells in BOX_MAP.items():
    for (r, c) in cells:
        CELL_TO_BOX[(r, c)] = b


class SudokuBoard:
    """9x9 standard sudoku board"""

    SIZE = 9
    EMPTY = 0
    DIGITS = set(range(1, 10))

    def __init__(self, grid: Optional[List[List[int]]] = None):
        if grid is None:
            self.grid = [[0] * 9 for _ in range(9)]
        else:
            assert len(grid) == 9 and all(len(row) == 9 for row in grid), \
                f"Expected 9x9 grid, got {len(grid)}x{len(grid[0]) if grid else 0}"
            for r in range(9):
                for c in range(9):
                    v = grid[r][c]
                    assert isinstance(v, int) and 0 <= v <= 9, \
                        f"Cell ({r},{c}) has invalid value {v}; must be 0-9"
            self.grid = [row[:] for row in grid]
        if not self._is_valid_internally():
            warnings.warn("Board contains conflicting clues (duplicate digits in row/col/box)")

    @classmethod
    def from_trusted(cls, grid: List[List[int]]) -> "SudokuBoard":
        """Create board with strict validation (raises ValueError on conflicts)"""
        board = cls(grid)
        if not board._is_valid_internally():
            raise ValueError("Board contains conflicting clues (duplicate digits in row/col/box)")
        return board

    @classmethod
    def from_string(cls, s: str) -> "SudokuBoard":
        """Create from ASCII string (9 lines, 9 chars each, 0=empty)"""
        lines = [ln.strip() for ln in s.strip().splitlines() if ln.strip()]
        assert len(lines) == 9, f"Need 9 lines, got {len(lines)}"
        grid = []
        for line in lines:
            row = []
            for ch in line.replace(" ", ""):
                if ch in "0.":
                    row.append(0)
                else:
                    row.append(int(ch))
            assert len(row) == 9
            grid.append(row)
        return cls(grid)

    def clone(self) -> "SudokuBoard":
        return SudokuBoard(self.grid)

    def is_solved(self) -> bool:
        """Check if fully solved"""
        return self.count_empty() == 0 and self.is_valid()

    def count_empty(self) -> int:
        return sum(row.count(0) for row in self.grid)

    def _is_valid_internally(self) -> bool:
        """Fast validity check for constructor (internal, no recursion)"""
        for r in range(9):
            seen = set()
            for v in self.grid[r]:
                if v != 0 and v in seen:
                    return False
                seen.add(v)
        for c in range(9):
            seen = set()
            for r in range(9):
                v = self.grid[r][c]
                if v != 0 and v in seen:
                    return False
                seen.add(v)
        for b in range(9):
            seen = set()
            for (r, c) in BOX_MAP[b]:
                v = self.grid[r][c]
                if v != 0 and v in seen:
                    return False
                seen.add(v)
        return True

    def is_valid(self) -> bool:
        """Check if board violates any constraint"""
        # Row check
        for r in range(9):
            seen = set()
            for v in self.grid[r]:
                if v != 0 and v in seen:
                    return False
                seen.add(v)
        # Column check
        for c in range(9):
            seen = set()
            for r in range(9):
                v = self.grid[r][c]
                if v != 0 and v in seen:
                    return False
                seen.add(v)
        # Box check
        for b in range(9):
            seen = set()
            for (r, c) in BOX_MAP[b]:
                v = self.grid[r][c]
                if v != 0 and v in seen:
                    return False
                seen.add(v)
        return True

    def get_candidates_rc(self):
        """Return 9x9 candidate sets for each cell"""
        cand = [[set(range(1, 10)) for _ in range(9)] for _ in range(9)]
        for r in range(9):
            for c in range(9):
                v = self.grid[r][c]
                if v != 0:
                    cand[r][c] = set()
                    for cc in range(9):
                        cand[r][cc].discard(v)
                    for rr in range(9):
                        cand[rr][c].discard(v)
                    for (rr, cc) in BOX_MAP[CELL_TO_BOX[(r, c)]]:
                        cand[rr][cc].discard(v)
        return cand

    def as_numpy(self) -> np.ndarray:
        return np.array(self.grid, dtype=np.int32)

    def __repr__(self) -> str:
        lines = []
        for r in range(9):
            line = ""
            for c in range(9):
                v = self.grid[r][c]
                line += str(v) if v != 0 else "."
                if c in (2, 5):
                    line += " | "
                else:
                    line += " "
            lines.append(line)
            if r in (2, 5):
                lines.append("------+-------+------")
        return "\n".join(lines)

    def __eq__(self, other):
        return self.grid == other.grid


# Test puzzles
PUZZLE_MINIMAL = SudokuBoard.from_string("""
    000000010
    400000000
    020000000
    000050407
    008000300
    001090000
    300400200
    050100000
    000806000
""")

PUZZLE_MEDIUM = SudokuBoard.from_string("""
    530070000
    600195000
    098000060
    800060003
    400803001
    700020006
    060000280
    000419005
    000080079
""")

PUZZLE_HARD = SudokuBoard.from_string("""
    800000000
    003600000
    070090200
    050007000
    000045700
    000100030
    001000068
    008500010
    090000400
""")

PUZZLE_AI_ESCARGOT = SudokuBoard.from_string("""
    100007090
    030020008
    009600500
    005300900
    010080002
    600004000
    300000010
    040000007
    007000300
""")

PUZZLE_COLLECTION = {
    "minimal": PUZZLE_MINIMAL,
    "medium": PUZZLE_MEDIUM,
    "hard": PUZZLE_HARD,
    "ai_escargot": PUZZLE_AI_ESCARGOT,
}
