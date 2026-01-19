"""
Poker decision-making engine (brain) for complete game play (preflop through river).

Implements comprehensive rule-based strategy with position awareness and hand reading.
"""

from typing import Tuple, List, Optional
from card import Card, Rank, Suit
from hand_eval import rank_hand
import random


# Preflop hand rankings for heads-up (169 unique hands)
# Format: (rank1, rank2, suited) -> percentile (0.0 to 1.0)
# Higher percentile = stronger hand

def _calculate_preflop_strength(hand: Tuple[Card, Card]) -> float:
    """
    Calculate preflop hand strength as a percentile (0.0 to 1.0).

    In heads-up poker, there are 169 unique starting hands:
    - 13 pocket pairs (AA, KK, ..., 22)
    - 78 suited hands (AKs, AQs, ..., 32s)
    - 78 offsuit hands (AKo, AQo, ..., 32o)

    Returns:
        Float between 0.0 (weakest) and 1.0 (strongest)
    """
    card1, card2 = hand
    rank1_val = card1.get_rank_value()
    rank2_val = card2.get_rank_value()
    is_pair = rank1_val == rank2_val
    is_suited = card1.suit == card2.suit

    # Normalize to high/low order
    high_rank = max(rank1_val, rank2_val)
    low_rank = min(rank1_val, rank2_val)

    if is_pair:
        # Pocket pairs: AA = 1.0, KK = 0.94, ..., 22 = 0.31
        pair_strength = {
            14: 1.00,  # AA
            13: 0.94,  # KK
            12: 0.88,  # QQ
            11: 0.82,  # JJ
            10: 0.76,  # TT
            9: 0.70,   # 99
            8: 0.64,   # 88
            7: 0.58,   # 77
            6: 0.52,   # 66
            5: 0.46,   # 55
            4: 0.40,   # 44
            3: 0.35,   # 33
            2: 0.31,   # 22
        }
        return pair_strength[high_rank]

    # Suited hands are stronger than offsuit
    if is_suited:
        # Premium suited: AKs, AQs, AJs, KQs, etc.
        if high_rank == 14:  # Ace high
            suited_strength = {
                13: 0.88,  # AKs
                12: 0.85,  # AQs
                11: 0.82,  # AJs
                10: 0.78,  # ATs
                9: 0.74,   # A9s
                8: 0.70,   # A8s
                7: 0.66,   # A7s
                6: 0.62,   # A6s
                5: 0.58,   # A5s
                4: 0.54,   # A4s
                3: 0.50,   # A3s
                2: 0.46,   # A2s
            }
            return suited_strength[low_rank]

        # King high suited
        if high_rank == 13:
            suited_strength = {
                12: 0.80,  # KQs
                11: 0.76,  # KJs
                10: 0.72,  # KTs
                9: 0.68,   # K9s
                8: 0.64,   # K8s
                7: 0.60,   # K7s
                6: 0.56,   # K6s
                5: 0.52,   # K5s
                4: 0.48,   # K4s
                3: 0.44,   # K3s
                2: 0.40,   # K2s
            }
            return suited_strength[low_rank]

        # Queen high suited
        if high_rank == 12:
            suited_strength = {
                11: 0.72,  # QJs
                10: 0.68,  # QTs
                9: 0.64,   # Q9s
                8: 0.60,   # Q8s
                7: 0.56,   # Q7s
                6: 0.52,   # Q6s
                5: 0.48,   # Q5s
                4: 0.44,   # Q4s
                3: 0.40,   # Q3s
                2: 0.36,   # Q2s
            }
            return suited_strength.get(low_rank, 0.30)

        # Lower suited hands - use a formula
        if high_rank >= 10:
            base = 0.60 - (high_rank - 10) * 0.08
            gap_penalty = (high_rank - low_rank - 1) * 0.04
            return max(0.20, base - gap_penalty)

        # Very low suited hands
        return max(0.15, 0.50 - (high_rank - 2) * 0.05)

    else:
        # Offsuit hands (weaker than suited)
        if high_rank == 14:  # Ace high offsuit
            offsuit_strength = {
                13: 0.82,  # AKo
                12: 0.78,  # AQo
                11: 0.74,  # AJo
                10: 0.70,  # ATo
                9: 0.66,   # A9o
                8: 0.62,   # A8o
                7: 0.58,   # A7o
                6: 0.54,   # A6o
                5: 0.50,   # A5o
                4: 0.46,   # A4o
                3: 0.42,   # A3o
                2: 0.38,   # A2o
            }
            return offsuit_strength[low_rank]

        # King high offsuit
        if high_rank == 13:
            offsuit_strength = {
                12: 0.72,  # KQo
                11: 0.68,  # KJo
                10: 0.64,  # KTo
                9: 0.60,   # K9o
                8: 0.56,   # K8o
                7: 0.52,   # K7o
                6: 0.48,   # K6o
                5: 0.44,   # K5o
                4: 0.40,   # K4o
                3: 0.36,   # K3o
                2: 0.32,   # K2o
            }
            return offsuit_strength.get(low_rank, 0.25)

        # Lower offsuit hands
        if high_rank >= 10:
            base = 0.50 - (high_rank - 10) * 0.08
            gap_penalty = (high_rank - low_rank - 1) * 0.05
            return max(0.10, base - gap_penalty)

        # Very low offsuit hands (like 72o)
        return max(0.05, 0.40 - (high_rank - 2) * 0.06)


def _is_premium_hand(hand_strength: float) -> bool:
    """Check if hand is premium (AA, KK, QQ, JJ, AK)."""
    return hand_strength >= 0.82  # Top ~15%


def _is_strong_hand(hand_strength: float) -> bool:
    """Check if hand is strong (top 15-35%)."""
    return 0.65 <= hand_strength < 0.82


def _is_medium_hand(hand_strength: float) -> bool:
    """Check if hand is medium (top 35-60%)."""
    return 0.40 <= hand_strength < 0.65


def _evaluate_postflop_hand(hole_cards: Tuple[Card, Card], board: List[Card]) -> Tuple[int, str, dict]:
    """
    Evaluate postflop hand strength.

    Returns:
        Tuple of (hand_rank, hand_description, metadata)
        - hand_rank: 1-10 (1=high card, 10=royal flush)
        - hand_description: Human-readable description
        - metadata: Additional info (e.g., top pair, draws)
    """
    if not board:
        return (0, "no board", {})

    all_cards = list(hole_cards) + board
    score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=list(hole_cards))

    hand_names = {
        10: "Royal Flush", 9: "Straight Flush", 8: "Quads",
        7: "Full House", 6: "Flush", 5: "Straight",
        4: "Trips", 3: "Two Pair", 2: "One Pair", 1: "High Card"
    }

    hand_desc = hand_names.get(score, "Unknown")

    # Check for draws
    draws = _check_for_draws(hole_cards, board)
    metadata.update(draws)

    # Determine hand category
    if score >= 5:  # Straight or better
        category = "made_hand"
    elif score == 4:  # Trips
        category = "strong"
    elif score == 3:  # Two pair
        category = "two_pair"  # Changed from "strong" for clarity
    elif score == 2:  # One pair
        # Classify pair strength relative to board
        pair_strength = _classify_pair_strength(hole_cards, board)

        if pair_strength == 'overpair':
            category = "overpair"
        elif pair_strength == 'top_pair':
            category = "top_pair"
        elif pair_strength == 'second_pair':
            category = "second_pair"
        elif pair_strength == 'third_pair':
            category = "third_pair"
        else:
            category = "underpair"

        metadata['pair_strength'] = pair_strength
    else:  # High card
        category = "high_card"

    metadata['category'] = category

    return (score, hand_desc, metadata)


def _classify_pair_strength(hole_cards: Tuple[Card, Card], board: List[Card]) -> str:
    """
    Classify pair strength relative to board.

    For pocket pairs, determines position relative to board:
    - Overpair: Higher than all board cards
    - Second pair: Between highest and second-highest board card
    - Third pair: Between second and third-highest board card
    - Underpair: Lower than all board cards

    For non-pocket pairs, determines which board card was paired:
    - Top pair: Paired highest board card
    - Second pair: Paired second-highest board card
    - Third pair: Paired third-highest board card
    - Underpair: Paired lower board card

    Returns:
        'overpair', 'top_pair', 'second_pair', 'third_pair', 'underpair', or 'no_pair'
    """
    if not board:
        return 'no_pair'

    # Get all unique board card ranks sorted high to low
    board_ranks = sorted(set([c.get_rank_value() for c in board]), reverse=True)

    card1, card2 = hole_cards

    # Check if we have a pocket pair
    if card1.get_rank_value() == card2.get_rank_value():
        pair_rank = card1.get_rank_value()

        # Overpair: pocket pair higher than all board cards
        if pair_rank > board_ranks[0]:
            return 'overpair'

        # Check if pocket pair ranks between board cards (e.g., KK on A-7-2 or Q-7-2)
        if len(board_ranks) > 1 and board_ranks[0] > pair_rank > board_ranks[1]:
            return 'second_pair'

        if len(board_ranks) > 2 and board_ranks[1] > pair_rank > board_ranks[2]:
            return 'third_pair'

        # Underpair: pocket pair lower than all board cards
        return 'underpair'

    # Not a pocket pair, check if we paired a board card
    for hole_card in hole_cards:
        hole_rank = hole_card.get_rank_value()

        if hole_rank == board_ranks[0]:
            return 'top_pair'
        elif len(board_ranks) > 1 and hole_rank == board_ranks[1]:
            return 'second_pair'
        elif len(board_ranks) > 2 and hole_rank == board_ranks[2]:
            return 'third_pair'
        elif hole_rank in board_ranks:
            return 'underpair'

    return 'no_pair'


def _is_top_pair(hole_cards: Tuple[Card, Card], board: List[Card], tiebreakers: List[int]) -> bool:
    """
    Check if we have top pair (pair with highest board card).
    DEPRECATED: Use _classify_pair_strength instead for more detailed classification.
    """
    if not board:
        return False

    # Get highest board card
    highest_board_rank = max(c.get_rank_value() for c in board)

    # Check if one of our hole cards matches
    for hole_card in hole_cards:
        if hole_card.get_rank_value() == highest_board_rank:
            return True

    return False


def _check_for_draws(hole_cards: Tuple[Card, Card], board: List[Card]) -> dict:
    """
    Check for flush draws and straight draws.

    Returns:
        Dictionary with draw information
    """
    draws = {
        'flush_draw': False,
        'oesd': False,  # Open-ended straight draw
        'gutshot': False,
    }

    if len(board) < 3:
        return draws

    all_cards = list(hole_cards) + board

    # Check for flush draw (4 to a flush)
    suit_counts = {}
    for card in all_cards:
        suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

    if max(suit_counts.values()) == 4:
        draws['flush_draw'] = True

    # Check for straight draws
    ranks = sorted(set(c.get_rank_value() for c in all_cards))

    # Check for open-ended straight draw (4 consecutive cards)
    for i in range(len(ranks) - 3):
        if ranks[i+3] - ranks[i] == 3:
            draws['oesd'] = True
            break

    # Check for gutshot (4 cards with one gap)
    for i in range(len(ranks) - 3):
        if ranks[i+3] - ranks[i] == 4:
            draws['gutshot'] = True
            break

    return draws


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
    Make a preflop poker decision.

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
        - action: "fold", "call", or "raise"
        - bet_size: Amount to bet
    """
    hand_strength = _calculate_preflop_strength(hand)

    # Check if hand qualifies for 4-bet range (only AA/KK/QQ/JJ/AK/A5s)
    card1, card2 = hand
    rank1 = card1.get_rank_value()
    rank2 = card2.get_rank_value()
    is_suited = card1.suit == card2.suit

    is_4bet_hand = (
        (rank1 == 14 and rank2 == 14) or  # AA
        (rank1 == 13 and rank2 == 13) or  # KK
        (rank1 == 12 and rank2 == 12) or  # QQ
        (rank1 == 11 and rank2 == 11) or  # JJ
        (rank1 == 14 and rank2 == 13) or  # AK
        (rank1 == 13 and rank2 == 14) or  # AK
        (rank1 == 14 and rank2 == 5 and is_suited) or  # A5s
        (rank1 == 5 and rank2 == 14 and is_suited)     # A5s
    )

    # Stack-to-pot ratio check - if raise is >= 1/4 of stack, only options are all-in or fold
    if raise_amount and raise_amount >= current_stack * 0.25:
        # Facing a large raise relative to stack
        if facing_4bet or (raise_amount >= current_stack):
            # Facing all-in
            if _is_premium_hand(hand_strength):
                return ("call", raise_amount)
            else:
                return ("fold", 0.0)
        else:
            # Large raise but not all-in - go all-in or fold
            if _is_premium_hand(hand_strength) or _is_strong_hand(hand_strength):
                return ("raise", current_stack)  # All-in
            else:
                return ("fold", 0.0)

    # Facing 4-bet (all-in)
    if facing_4bet:
        if _is_premium_hand(hand_strength):
            return ("call", raise_amount if raise_amount else current_stack)
        else:
            return ("fold", 0.0)

    # Facing 3-bet
    if facing_3bet:
        if is_4bet_hand:
            # 4-bet all-in
            return ("raise", current_stack)
        elif _is_strong_hand(hand_strength):
            # Call with strong hands
            return ("call", raise_amount if raise_amount else 3.0 * big_blind)
        else:
            return ("fold", 0.0)

    # Facing first raise
    if facing_raise and not facing_3bet:
        if _is_premium_hand(hand_strength):
            # 3-bet to 3x the raise
            return ("raise", (raise_amount if raise_amount else 3.0 * big_blind) * 3.0)
        elif _is_strong_hand(hand_strength) or _is_medium_hand(hand_strength):
            # Call with strong and medium hands
            return ("call", raise_amount if raise_amount else 3.0 * big_blind)
        else:
            # Fold weak hands
            return ("fold", 0.0)

    # First to act (can raise first-in)
    if is_first_to_act:
        # Raise top 60% of hands
        if hand_strength >= 0.40:  # Top 60%
            return ("raise", 3.0 * big_blind)
        else:
            return ("fold", 0.0)

    # Should not reach here in normal flow
    return ("fold", 0.0)


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
    Make a postflop decision (flop, turn, or river).

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
    # Evaluate hand strength
    score, hand_desc, metadata = _evaluate_postflop_hand(hand, board)
    category = metadata.get('category', 'unknown')
    has_flush_draw = metadata.get('flush_draw', False)
    has_oesd = metadata.get('oesd', False)
    has_gutshot = metadata.get('gutshot', False)
    has_draw = has_flush_draw or has_oesd or has_gutshot

    # Determine betting strategy based on street and position
    if street == "flop":
        return _make_flop_decision(
            score, category, has_draw, pot, current_stack,
            is_in_position, is_preflop_aggressor, facing_bet, bet_amount
        )
    elif street == "turn":
        return _make_turn_decision(
            score, category, has_draw, pot, current_stack,
            is_in_position, facing_bet, bet_amount
        )
    elif street == "river":
        return _make_river_decision(
            score, category, pot, current_stack,
            is_in_position, facing_bet, bet_amount
        )

    return ("check", 0.0)


def _make_flop_decision(
    score: int,
    category: str,
    has_draw: bool,
    pot: float,
    stack: float,
    in_position: bool,
    is_aggressor: bool,
    facing_bet: bool,
    bet_amount: float
) -> Tuple[str, float]:
    """Make decision on the flop."""

    if in_position:
        # IN POSITION (last to act)

        if facing_bet:
            # Facing all-in
            if bet_amount and bet_amount >= stack:
                # Call with top pair or better (including overpair, two pair, trips, made hands)
                if category in ['made_hand', 'strong', 'two_pair', 'overpair', 'top_pair']:
                    return ("call", bet_amount)
                else:
                    return ("fold", 0.0)
            # Facing normal bet
            else:
                # Call or fold based on hand strength
                if category in ['made_hand', 'strong', 'two_pair', 'overpair', 'top_pair']:
                    return ("call", bet_amount if bet_amount else 0.0)
                else:
                    return ("fold", 0.0)

        else:
            # Not facing a bet
            if is_aggressor:
                # C-bet (continuation bet) as preflop aggressor
                # Bet half pot or third pot (randomly choose)
                bet_size = pot * (0.5 if random.random() < 0.5 else 0.33)
                return ("raise", bet_size)
            else:
                # Not the aggressor, opponent checked
                if category in ['made_hand', 'strong', 'two_pair', 'overpair', 'top_pair']:
                    bet_size = pot * 0.66
                    return ("raise", bet_size)
                else:
                    return ("check", 0.0)

    else:
        # OUT OF POSITION (first to act)

        # Check-raise all-in with two pair or better
        if score >= 3:  # Two pair or better (includes trips, boats, straights, etc.)
            if facing_bet:
                return ("raise", stack)  # All-in
            else:
                return ("check", 0.0)

        # Check-call with overpair, top pair, or any draw
        elif category in ['overpair', 'top_pair'] or has_draw:
            if facing_bet:
                return ("call", bet_amount if bet_amount else 0.0)
            else:
                return ("check", 0.0)

        # Check-fold with high card, second pair, or weaker
        else:
            if facing_bet:
                return ("fold", 0.0)
            else:
                return ("check", 0.0)


def _make_turn_decision(
    score: int,
    category: str,
    has_draw: bool,
    pot: float,
    stack: float,
    in_position: bool,
    facing_bet: bool,
    bet_amount: float
) -> Tuple[str, float]:
    """Make decision on the turn."""

    if in_position:
        # IN POSITION

        # Bet pot with overpair, top pair, or better
        if category in ['overpair', 'top_pair'] or score >= 3:  # Overpair, top pair, two pair, or better
            if facing_bet:
                return ("call", bet_amount if bet_amount else 0.0)
            else:
                # Bet pot size
                return ("raise", pot)

        else:
            # Worse than top pair (including second pair and draws)
            if facing_bet:
                return ("fold", 0.0)
            else:
                return ("check", 0.0)

    else:
        # OUT OF POSITION

        if score >= 5:  # Made hand (straight or better)
            # Check-raise all-in
            if facing_bet:
                return ("raise", stack)
            else:
                return ("check", 0.0)

        elif category in ['overpair', 'top_pair'] or score in [3, 4]:  # Overpair, top pair, two pair, or trips
            # Check-call any size bet
            if facing_bet:
                return ("call", bet_amount if bet_amount else 0.0)
            else:
                return ("check", 0.0)

        else:
            # Worse than top pair (second pair, third pair, underpair, high card)
            if facing_bet:
                return ("fold", 0.0)
            else:
                return ("check", 0.0)


def _make_river_decision(
    score: int,
    category: str,
    pot: float,
    stack: float,
    in_position: bool,
    facing_bet: bool,
    bet_amount: float
) -> Tuple[str, float]:
    """Make decision on the river."""

    if in_position:
        # IN POSITION

        if score >= 5:  # Straight or better
            # Raise all-in (or bet all-in if not facing a bet)
            if facing_bet:
                return ("raise", stack)
            else:
                return ("raise", stack)

        else:
            # Check back with any other hand
            if facing_bet:
                # Call with overpair, top pair, two pair, or trips
                if category in ['overpair', 'top_pair', 'two_pair', 'strong'] or score == 4:
                    return ("call", bet_amount if bet_amount else 0.0)
                else:
                    return ("fold", 0.0)
            else:
                return ("check", 0.0)

    else:
        # OUT OF POSITION

        if score >= 5:  # Straight or better
            # Check-raise all-in
            if facing_bet:
                return ("raise", stack)
            else:
                return ("check", 0.0)

        elif category in ['overpair', 'top_pair', 'two_pair', 'strong'] or score in [3, 4]:
            # Check-call with overpair, top pair, two pair, or trips
            if facing_bet:
                return ("call", bet_amount if bet_amount else 0.0)
            else:
                return ("check", 0.0)

        else:
            # Check-fold with second pair or worse
            if facing_bet:
                return ("fold", 0.0)
            else:
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
    is_button = position >= 1
    is_first_to_act = is_button

    current_stack = stack_depth if stack_depth else 1000.0

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
    print("Poker Brain - Comprehensive Decision Making Test")
    print("=" * 60)
    print()

    # Test 1: Preflop - Premium hand facing 3-bet
    print("Test 1: AA facing 3-bet")
    print("-" * 60)
    hand_aa = create_hand('As', 'Ah')
    action, bet_size = make_preflop_decision(
        hand_aa, position=1, pot=0, current_stack=1000, big_blind=10,
        facing_raise=True, raise_amount=30, facing_3bet=True
    )
    print(f"Hand: {hand_aa[0]}, {hand_aa[1]}")
    print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
    print("Expected: RAISE (4-bet all-in)")
    print("✓ PASSED" if action == "raise" and bet_size == 1000 else "✗ FAILED")
    print()

    # Test 2: Postflop - Top pair on flop OOP
    print("Test 2: Top pair on flop, out of position")
    print("-" * 60)
    hand_ak = create_hand('Ah', 'Kd')
    board_flop = [Card.from_string('As'), Card.from_string('7h'), Card.from_string('2c')]
    action, bet_size = make_postflop_decision(
        hand_ak, board_flop, position=0, pot=60, current_stack=1000,
        is_in_position=False, facing_bet=True, bet_amount=30, street="flop"
    )
    print(f"Hand: {hand_ak[0]}, {hand_ak[1]}")
    print(f"Board: {', '.join(str(c) for c in board_flop)}")
    print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
    print("Expected: CALL (check-call with top pair)")
    print("✓ PASSED" if action == "call" else "✗ FAILED")
    print()

    # Test 3: Postflop - Made straight on turn in position
    print("Test 3: Made straight on turn, in position")
    print("-" * 60)
    hand_jt = create_hand('Jh', '10d')
    board_turn = [
        Card.from_string('Qs'), Card.from_string('9h'),
        Card.from_string('2c'), Card.from_string('8s')
    ]
    action, bet_size = make_postflop_decision(
        hand_jt, board_turn, position=1, pot=120, current_stack=900,
        is_in_position=True, facing_bet=False, street="turn"
    )
    print(f"Hand: {hand_jt[0]}, {hand_jt[1]}")
    print(f"Board: {', '.join(str(c) for c in board_turn)}")
    print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
    print("Expected: RAISE (bet pot with straight)")
    print("✓ PASSED" if action == "raise" and bet_size == 120 else "✗ FAILED")
    print()

    print("=" * 60)
    print("Basic tests completed!")
    print("=" * 60)
