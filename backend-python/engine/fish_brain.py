"""
Fish poker agent - A passive calling station for simulation testing.

The "fish" playstyle:
- Preflop: Never raises, never folds. Always limps (calls).
- Postflop OOP (out of position): Always check-call (check, then call any bet)
- Postflop IP (in position): Always check back (never bet)
- Never raises at any point in the hand
"""

from typing import Tuple, List
from card import Card


def make_preflop_decision(
    hand: Tuple[Card, Card],
    position: int,
    pot: float,
    current_stack: float,
    big_blind: float = 10.0,
    facing_raise: bool = False,
    raise_amount: float = None,
    facing_3bet: bool = False,
    facing_4bet: bool = False,
    is_first_to_act: bool = True
) -> Tuple[str, float]:
    """
    Make a preflop poker decision for the fish agent.

    Fish behavior preflop:
    - Never folds preflop
    - Never raises preflop
    - Always calls/limps

    Args:
        hand: Tuple of two Card objects
        position: Position at table (0 = BB, 1+ = Button)
        pot: Current pot size
        current_stack: Player's current stack
        big_blind: Big blind size
        facing_raise: Whether facing a raise
        raise_amount: Amount needed to call if facing raise
        facing_3bet: Whether facing a 3-bet
        facing_4bet: Whether facing a 4-bet
        is_first_to_act: Whether first to act preflop

    Returns:
        Tuple of (action, bet_size)
        - action: "call" (fish never folds or raises preflop)
        - bet_size: Amount to call
    """
    # Fish always calls preflop - never folds, never raises
    if facing_raise or facing_3bet or facing_4bet:
        # Call any raise amount (even if it means all-in)
        call_amount = raise_amount if raise_amount else big_blind
        call_amount = min(call_amount, current_stack)
        return ("call", call_amount)

    # First to act or no raise - limp (call big blind)
    if is_first_to_act:
        # Limp in (call the big blind)
        return ("call", big_blind)

    # Default: call
    return ("call", big_blind)


def make_postflop_decision(
    hand: Tuple[Card, Card],
    board: List[Card],
    position: int,
    pot: float,
    current_stack: float,
    big_blind: float = 10.0,
    is_in_position: bool = True,
    is_preflop_aggressor: bool = False,
    facing_bet: bool = False,
    bet_amount: float = None,
    street: str = "flop"
) -> Tuple[str, float]:
    """
    Make a postflop decision for the fish agent.

    Fish behavior postflop:
    - Out of position: Check, then call any bet (check-call)
    - In position: Check back (never bet)
    - Never raises postflop

    Args:
        hand: Tuple of two hole cards
        board: List of community cards
        position: Player position
        pot: Current pot size
        current_stack: Player's stack
        big_blind: Big blind size
        is_in_position: Whether player is in position (last to act)
        is_preflop_aggressor: Whether player was last raiser preflop
        facing_bet: Whether facing a bet
        bet_amount: Amount of bet being faced
        street: Current street ("flop", "turn", "river")

    Returns:
        Tuple of (action, bet_size)
    """
    if is_in_position:
        # IN POSITION: Check back (never bet)
        if facing_bet:
            # Call any bet (fish calls everything)
            call_amount = bet_amount if bet_amount else 0.0
            call_amount = min(call_amount, current_stack)
            return ("call", call_amount)
        else:
            # Not facing a bet - check back
            return ("check", 0.0)

    else:
        # OUT OF POSITION: Check-call
        if facing_bet:
            # Call any bet
            call_amount = bet_amount if bet_amount else 0.0
            call_amount = min(call_amount, current_stack)
            return ("call", call_amount)
        else:
            # Not facing a bet - check
            return ("check", 0.0)


# Legacy compatibility function
def make_decision(
    hand: Tuple[Card, Card],
    position: int,
    pot_odds: float = None,
    stack_depth: float = None,
    big_blind: float = 10.0,
    facing_raise: bool = False,
    raise_amount: float = None
) -> Tuple[str, float]:
    """
    Legacy function for backward compatibility.
    Only handles preflop decisions.
    """
    current_stack = stack_depth if stack_depth else 1000.0
    is_button = position >= 1
    is_first_to_act = is_button

    return make_preflop_decision(
        hand=hand,
        position=position,
        pot=0.0,
        current_stack=current_stack,
        big_blind=big_blind,
        facing_raise=facing_raise,
        raise_amount=raise_amount,
        facing_3bet=False,
        facing_4bet=False,
        is_first_to_act=is_first_to_act
    )


if __name__ == "__main__":
    from card import Card, create_hand

    print("=" * 60)
    print("Fish Brain - Passive Calling Station Test")
    print("=" * 60)
    print()

    # Test 1: Preflop - Fish never folds, always calls
    print("Test 1: Fish preflop behavior (should always call)")
    print("-" * 60)

    # Test with weak hand - fish should still call
    hand_72o = create_hand('7s', '2h')  # Worst hand in poker
    action, bet_size = make_preflop_decision(
        hand_72o, position=1, pot=15, current_stack=1000, big_blind=10,
        facing_raise=True, raise_amount=30
    )
    print(f"Hand: 7-2 offsuit facing 3x raise")
    print(f"Decision: {action.upper()}, Amount: ${bet_size:.2f}")
    print("Expected: CALL (fish never folds)")
    print("PASSED" if action == "call" else "FAILED")
    print()

    # Test 2: Fish limps when first to act
    print("Test 2: Fish limps when first to act")
    print("-" * 60)
    hand_aa = create_hand('As', 'Ah')  # Best hand
    action, bet_size = make_preflop_decision(
        hand_aa, position=1, pot=15, current_stack=1000, big_blind=10,
        facing_raise=False, is_first_to_act=True
    )
    print(f"Hand: AA first to act (should limp, not raise)")
    print(f"Decision: {action.upper()}, Amount: ${bet_size:.2f}")
    print("Expected: CALL (fish never raises, even with AA)")
    print("PASSED" if action == "call" else "FAILED")
    print()

    # Test 3: Postflop - Fish check-calls OOP
    print("Test 3: Fish check-calls out of position")
    print("-" * 60)
    board_flop = [Card.from_string('As'), Card.from_string('7h'), Card.from_string('2c')]
    action, bet_size = make_postflop_decision(
        hand_aa, board_flop, position=0, pot=60, current_stack=1000,
        is_in_position=False, facing_bet=True, bet_amount=30, street="flop"
    )
    print(f"Hand: AA on A-7-2 board, OOP, facing $30 bet")
    print(f"Decision: {action.upper()}, Amount: ${bet_size:.2f}")
    print("Expected: CALL (fish check-calls)")
    print("PASSED" if action == "call" else "FAILED")
    print()

    # Test 4: Postflop - Fish checks back IP
    print("Test 4: Fish checks back in position")
    print("-" * 60)
    action, bet_size = make_postflop_decision(
        hand_aa, board_flop, position=1, pot=60, current_stack=1000,
        is_in_position=True, facing_bet=False, street="flop"
    )
    print(f"Hand: AA on A-7-2 board, IP, opponent checked")
    print(f"Decision: {action.upper()}, Amount: ${bet_size:.2f}")
    print("Expected: CHECK (fish checks back)")
    print("PASSED" if action == "check" else "FAILED")
    print()

    # Test 5: Fish calls all-in
    print("Test 5: Fish calls all-in")
    print("-" * 60)
    action, bet_size = make_preflop_decision(
        hand_72o, position=0, pot=1015, current_stack=990, big_blind=10,
        facing_raise=True, raise_amount=1000, facing_4bet=True
    )
    print(f"Hand: 7-2 offsuit facing all-in ($1000)")
    print(f"Decision: {action.upper()}, Amount: ${bet_size:.2f}")
    print("Expected: CALL (fish calls everything)")
    print("PASSED" if action == "call" else "FAILED")
    print()

    print("=" * 60)
    print("Fish brain tests completed!")
    print("=" * 60)
