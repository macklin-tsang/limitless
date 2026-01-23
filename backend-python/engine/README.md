# Limitless Poker Engine - Backend Python

## Phase 1, Step 5: Complete Implementation ✓

This directory contains a complete poker game engine with comprehensive player tendencies implementing logically sound poker strategy.

## Quick Start

### Run Tests
```bash
# Test option logic (cannot fold when have option)
python3 test_option_logic.py

# Test priority fixes (overpair, two-pair)
python3 test_fixes.py

# Test game engine
python3 test_game_demo.py
```

### Run a Game
```bash
python3 game.py
```

## Key Files

### Core Engine
- **[game.py](game.py)** - Complete poker game engine with betting rounds, showdown, pot management
- **[brain.py](brain.py)** - Comprehensive player decision logic with preflop and postflop strategies
- **[fish_brain.py](fish_brain.py)** - Passive calling station agent for testing
- **[card.py](card.py)** - Card representation (Rank, Suit, Card classes)
- **[hand_eval.py](hand_eval.py)** - Hand evaluation and ranking

### Tests
- **[test_option_logic.py](test_option_logic.py)** - Validates "option" rule compliance
- **[test_fixes.py](test_fixes.py)** - Validates overpair and two-pair fixes
- **[test_game_demo.py](test_game_demo.py)** - Game engine demonstration

### Documentation
- **[STEP5_SUMMARY.md](STEP5_SUMMARY.md)** - Complete implementation summary
- **[OPTION_FIX.md](OPTION_FIX.md)** - Option logic fix details
- **[POSTFLOP_FIX.md](POSTFLOP_FIX.md)** - Postflop integration fix details

## Implementation Highlights

### Preflop Strategy
- ✅ First-in raise: 3x BB with top 60% of hands
- ✅ Never limps when first to act
- ✅ 3-bet top 15%, 4-bet premium hands only
- ✅ Option logic: Cannot fold when BB has option

### Postflop Strategy
- ✅ Position-aware (IP vs OOP)
- ✅ Hand-strength-based decisions
- ✅ Dynamic overpair classification
- ✅ Pot-relative bet sizing (66%/75%/100%)

### Critical Fixes
- ✅ Overpair classification with automatic downgrades
- ✅ Two-pair check-raise all-in
- ✅ Postflop integration (routing to correct decision function)
- ✅ Option logic (cannot fold when have option)

## Test Results

All tests passing ✓

```
TEST 1: BB Cannot Fold With Option         ✓ PASSED
TEST 2: BB CAN Fold Facing Raise           ✓ PASSED
TEST 3: Button CAN Open-Fold               ✓ PASSED
TEST 4: BB Raises Strong Hand With Option  ✓ PASSED
TEST 5: Cannot Fold When Opponent Checks   ✓ PASSED
TEST 6: CAN Fold Facing Bet                ✓ PASSED
TEST 7: Fish Brain Never Folds             ✓ PASSED
```

## Next Steps

Phase 1, Step 6: Python Simulation Runner
- Run N games between agents
- Track statistics (win rate, profit/loss)
- Save results to CSV

---

*Implementation completed: 2026-01-20*
