"""
Hand strength evaluation functions for poker decision-making.

Provides preflop and postflop hand strength calculations, hand classification,
and draw detection for Texas Hold'em poker.
"""

from typing import Tuple, List
from card import Card
from hand_eval import rank_hand


def calculate_preflop_strength(hand: Tuple[Card, Card]) -> float:
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


def is_premium_hand(hand_strength: float) -> bool:
    """Check if hand is premium (AA, KK, QQ, JJ, AK)."""
    return hand_strength >= 0.82  # Top ~15%


def is_strong_hand(hand_strength: float) -> bool:
    """Check if hand is strong (top 15-35%)."""
    return 0.65 <= hand_strength < 0.82


def is_medium_hand(hand_strength: float) -> bool:
    """Check if hand is medium (top 35-60%)."""
    return 0.40 <= hand_strength < 0.65


def evaluate_postflop_hand(hole_cards: Tuple[Card, Card], board: List[Card]) -> Tuple[int, str, dict]:
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
    draws = check_for_draws(hole_cards, board)
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
        pair_strength = classify_pair_strength(hole_cards, board)

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


def classify_pair_strength(hole_cards: Tuple[Card, Card], board: List[Card]) -> str:
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


def is_top_pair(hole_cards: Tuple[Card, Card], board: List[Card], tiebreakers: List[int]) -> bool:
    """
    Check if we have top pair (pair with highest board card).
    DEPRECATED: Use classify_pair_strength instead for more detailed classification.
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


def check_for_draws(hole_cards: Tuple[Card, Card], board: List[Card]) -> dict:
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


if __name__ == "__main__":
    """
    Test hand strength evaluation functions.
    """
    from card import create_hand, Card

    print("=" * 60)
    print("Hand Strength Evaluation Tests")
    print("=" * 60)
    print()

    # Test 1: Preflop strength
    print("Test 1: Preflop Strength")
    print("-" * 60)

    test_hands = [
        ("As", "Ah", "AA (pocket aces)"),
        ("Ah", "Kh", "AKs (ace-king suited)"),
        ("Ah", "Kd", "AKo (ace-king offsuit)"),
        ("7h", "2d", "72o (worst hand)"),
    ]

    for card1_str, card2_str, description in test_hands:
        hand = create_hand(card1_str, card2_str)
        strength = calculate_preflop_strength(hand)
        category = (
            "Premium" if is_premium_hand(strength)
            else "Strong" if is_strong_hand(strength)
            else "Medium" if is_medium_hand(strength)
            else "Weak"
        )
        print(f"  {description}: {strength:.2f} ({category})")

    print()

    # Test 2: Postflop evaluation
    print("Test 2: Postflop Evaluation")
    print("-" * 60)

    hole_cards = create_hand("Ah", "Kh")
    board = [Card.from_string("Kd"), Card.from_string("7h"), Card.from_string("2c")]

    rank, desc, metadata = evaluate_postflop_hand(hole_cards, board)
    print(f"  Hole: {hole_cards[0]}, {hole_cards[1]}")
    print(f"  Board: {', '.join(str(c) for c in board)}")
    print(f"  Hand: {desc} (rank {rank})")
    print(f"  Category: {metadata.get('category', 'unknown')}")
    print(f"  Pair strength: {metadata.get('pair_strength', 'N/A')}")
    print()

    # Test 3: Draw detection
    print("Test 3: Draw Detection")
    print("-" * 60)

    hole_cards = create_hand("Ah", "Kh")
    board = [Card.from_string("2h"), Card.from_string("5h"), Card.from_string("9c")]

    draws = check_for_draws(hole_cards, board)
    print(f"  Hole: {hole_cards[0]}, {hole_cards[1]}")
    print(f"  Board: {', '.join(str(c) for c in board)}")
    print(f"  Flush draw: {draws['flush_draw']}")
    print(f"  OESD: {draws['oesd']}")
    print(f"  Gutshot: {draws['gutshot']}")
    print()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
