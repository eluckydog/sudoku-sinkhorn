========================================================================
  SUDOKU FIELD - Cross-Engine Comparison Report
========================================================================

------------------------------------------------------------------------
  Puzzle: minimal (clues: 17)
------------------------------------------------------------------------
  Board:
    . . . | . . . | . 1 . 
    4 . . | . . . | . . . 
    . 2 . | . . . | . . . 
    ------+-------+------
    . . . | . 5 . | 4 . 7 
    . . 8 | . . . | 3 . . 
    . . 1 | . 9 . | . . . 
    ------+-------+------
    3 . . | 4 . . | 2 . . 
    . 5 . | 1 . . | . . . 
    . . . | 8 . 6 | . . . 

  > Results:
    [PASS] sinkhorn             | time=0.858s | iters=  500 | E=5.44e-08
    [FAIL] genetic_algorithm    | time=9.977s | iters=    0 | E=9.99e+02
    [FAIL] simulated_annealing  | time=31.638s | iters= 3000 | E=4.00e+00
    [FAIL] gradient_flow        | time=5.587s | iters= 2674 | E=8.26e+01
    [FAIL] belief_propagation   | time=0.213s | iters=  100 | E=9.99e+02

  > Sinkhorn phase transition: T_c = 0.7586

  > Unsolved engines: genetic_algorithm, simulated_annealing, gradient_flow, belief_propagation
    Hint: this puzzle has global-level difficulty


------------------------------------------------------------------------
  Puzzle: medium (clues: 30)
------------------------------------------------------------------------
  Board:
    5 3 . | . 7 . | . . . 
    6 . . | 1 9 5 | . . . 
    . 9 8 | . . . | . 6 . 
    ------+-------+------
    8 . . | . 6 . | . . 3 
    4 . . | 8 . 3 | . . 1 
    7 . . | . 2 . | . . 6 
    ------+-------+------
    . 6 . | . . . | 2 8 . 
    . . . | 4 1 9 | . . 5 
    . . . | . 8 . | . 7 9 

  > Results:
    [PASS] sinkhorn             | time=0.902s | iters=  500 | E=9.60e-08
    [FAIL] genetic_algorithm    | time=12.478s | iters=    0 | E=9.99e+02
    [FAIL] simulated_annealing  | time=30.371s | iters= 3000 | E=2.00e+00
    [FAIL] gradient_flow        | time=5.121s | iters= 2418 | E=1.42e+02
    [FAIL] belief_propagation   | time=0.241s | iters=  100 | E=9.99e+02

  > Sinkhorn phase transition: T_c = 0.9120

  > Unsolved engines: genetic_algorithm, simulated_annealing, gradient_flow, belief_propagation
    Hint: this puzzle has global-level difficulty


------------------------------------------------------------------------
  Puzzle: hard (clues: 21)
------------------------------------------------------------------------
  Board:
    8 . . | . . . | . . . 
    . . 3 | 6 . . | . . . 
    . 7 . | . 9 . | 2 . . 
    ------+-------+------
    . 5 . | . . 7 | . . . 
    . . . | . 4 5 | 7 . . 
    . . . | 1 . . | . 3 . 
    ------+-------+------
    . . 1 | . . . | . 6 8 
    . . 8 | 5 . . | . 1 . 
    . 9 . | . . . | 4 . . 

  > Results:
    [FAIL] sinkhorn             | time=0.919s | iters=  500 | E=3.40e+01
    [FAIL] genetic_algorithm    | time=12.218s | iters=    0 | E=9.99e+02
    [FAIL] simulated_annealing  | time=42.178s | iters= 3000 | E=2.00e+00
    [FAIL] gradient_flow        | time=5.678s | iters= 2396 | E=1.01e+02
    [FAIL] belief_propagation   | time=0.212s | iters=  100 | E=9.99e+02

  > Sinkhorn phase transition: T_c = 0.6310

  > Unsolved engines: sinkhorn, genetic_algorithm, simulated_annealing, gradient_flow, belief_propagation
    Hint: this puzzle has global-level difficulty


------------------------------------------------------------------------
  Puzzle: ai_escargot (clues: 23)
------------------------------------------------------------------------
  Board:
    1 . . | . . 7 | . 9 . 
    . 3 . | . 2 . | . . 8 
    . . 9 | 6 . . | 5 . . 
    ------+-------+------
    . . 5 | 3 . . | 9 . . 
    . 1 . | . 8 . | . . 2 
    6 . . | . . 4 | . . . 
    ------+-------+------
    3 . . | . . . | . 1 . 
    . 4 . | . . . | . . 7 
    . . 7 | . . . | 3 . . 

  > Results:
    [FAIL] sinkhorn             | time=0.873s | iters=  500 | E=7.40e+01
    [FAIL] genetic_algorithm    | time=13.556s | iters=    0 | E=9.99e+02
    [FAIL] simulated_annealing  | time=30.652s | iters= 3000 | E=2.00e+00
    [FAIL] gradient_flow        | time=4.691s | iters= 2260 | E=1.10e+02
    [FAIL] belief_propagation   | time=0.211s | iters=  100 | E=9.99e+02

  > Sinkhorn phase transition: T_c = 0.6310

  > Unsolved engines: sinkhorn, genetic_algorithm, simulated_annealing, gradient_flow, belief_propagation
    Hint: this puzzle has global-level difficulty

========================================================================
  NEW INSIGHTS
========================================================================

  [Insight 1] Difficulty classification: global vs algorithm-blind
    Puzzles unsolved by ALL engines -> global difficulty
    Puzzles solved by SOME engines -> algorithm-blind spots exist

  [Insight 2] Sinkhorn phase transition mapping
    'minimal' critical T_c = 0.7586
    Higher T_c = constraints lock in early -> easier puzzle
    Lower T_c = needs deep annealing -> harder puzzle

  [Insight 3] Engine convergence profiles