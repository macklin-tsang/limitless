"""
Hand evaluation functions for Texas Hold'em poker.

This module provides functions to evaluate and rank poker hands using numeric scoring.
Hand rankings:
    Royal Flush = 10
    Straight Flush = 9
    Quads = 8
    Boat = 7
    Flush = 6
    Straight = 5
    Trips = 4
    Two Pair = 3
    One Pair = 2
    High Card = 1
"""

from collections import Counter
from typing import List, Tuple
from card import Card, Rank, Suit


def rank_hand(cards: List[Card], hole_cards: List[Card] = None) -> Tuple[int, List[int], dict]:
    """
    Rank a poker hand and return numeric score with tiebreakers.
    
    Args:
        cards: List of Card objects (typically 5 or 7 cards for Texas Hold'em)
        hole_cards: Optional list of 2 hole cards. If provided, enables set vs trips detection.
    
    Returns:
        Tuple of (hand_rank_score, tiebreakers, metadata) where:
        - hand_rank_score: Integer from 1-10 representing hand strength
        - tiebreakers: List of integers used to break ties between same hand types
        - metadata: Dictionary with additional info (e.g., 'trips_type': 'set' or 'trips')
    
    Hand Rankings:
        10 = Royal Flush
        9 = Straight Flush
        8 = Quads
        7 = Boat
        6 = Flush
        5 = Straight
        4 = Trips
        3 = Two Pair
        2 = One Pair
        1 = High Card
    
    Examples:
        >>> cards = [Card.from_string('As'), Card.from_string('Ks'), Card.from_string('Qs'), 
        ...          Card.from_string('Js'), Card.from_string('10s')]
        >>> rank_hand(cards)
        (10, [14, 13, 12, 11, 10], {})
        
        >>> cards = [Card.from_string('Ah'), Card.from_string('2h'), Card.from_string('3h'),
        ...          Card.from_string('4h'), Card.from_string('5h')]
        >>> rank_hand(cards)
        (9, [5], {})
    """
    if not cards:
        raise ValueError("Cannot rank empty hand")
    
    if len(cards) < 5:
        raise ValueError(f"Need at least 5 cards to rank a hand, got {len(cards)}")
    
    # Check for duplicate cards
    card_set = set(cards)
    if len(card_set) != len(cards):
        duplicates = []
        seen = set()
        for card in cards:
            if card in seen:
                duplicates.append(str(card))
            seen.add(card)
        raise ValueError(f"Duplicate cards detected: {', '.join(duplicates)}. Each card can only appear once.")
    
    # Validate hole_cards if provided
    metadata = {}
    board_cards = None
    if hole_cards is not None:
        if len(hole_cards) != 2:
            raise ValueError(f"hole_cards must contain exactly 2 cards, got {len(hole_cards)}")
        # Check that hole cards are in the cards list
        hole_set = set(hole_cards)
        cards_set = set(cards)
        if not hole_set.issubset(cards_set):
            raise ValueError("hole_cards must be a subset of cards")
        # Get board cards (all cards minus hole cards)
        board_cards = [c for c in cards if c not in hole_set]
    
    # Get best 5-card hand from the available cards
    best_hand = _get_best_five_card_hand(cards)
    
    # Check if board chops (best hand uses only board cards, no hole cards)
    if hole_cards is not None and board_cards is not None and len(board_cards) >= 5:
        board_set = set(board_cards)
        best_hand_set = set(best_hand)
        if best_hand_set.issubset(board_set):
            metadata['board_chop'] = True
            metadata['hole_cards_play'] = False
        else:
            metadata['board_chop'] = False
            metadata['hole_cards_play'] = True
    
    # Check for each hand type in descending order of strength
    if _is_royal_flush(best_hand):
        return (10, [14, 13, 12, 11, 10], metadata)
    
    straight_flush_result = _is_straight_flush(best_hand)
    if straight_flush_result:
        return (9, [straight_flush_result], metadata)
    
    quads_result = _is_quads(best_hand)
    if quads_result:
        return (8, quads_result, metadata)
    
    boat_result = _is_boat(best_hand)
    if boat_result:
        return (7, boat_result, metadata)
    
    flush_result = _is_flush(best_hand)
    if flush_result:
        return (6, flush_result, metadata)
    
    straight_result = _is_straight(best_hand)
    if straight_result:
        return (5, [straight_result], metadata)
    
    trips_result = _is_trips(best_hand)
    if trips_result:
        # Determine if it's a set or trips if hole_cards provided
        if hole_cards is not None:
            trips_type = _determine_trips_type(best_hand, hole_cards, cards)
            metadata['trips_type'] = trips_type
        return (4, trips_result, metadata)
    
    two_pair_result = _is_two_pair(best_hand)
    if two_pair_result:
        return (3, two_pair_result, metadata)
    
    one_pair_result = _is_one_pair(best_hand)
    if one_pair_result:
        return (2, one_pair_result, metadata)
    
    # High card
    high_card_result = _get_high_card(best_hand)
    return (1, high_card_result, metadata)


def _get_best_five_card_hand(cards: List[Card]) -> List[Card]:
    """
    Get the best 5-card hand from a list of cards (for Texas Hold'em with 7 cards).
    Uses brute force to check all combinations.
    """
    if len(cards) == 5:
        return sorted(cards, key=lambda c: c.get_rank_value(), reverse=True)
    
    # For more than 5 cards, find the best 5-card combination
    from itertools import combinations
    
    best_hand = None
    best_score = (0, [])
    
    for combo in combinations(cards, 5):
        combo_list = list(combo)
        score = _evaluate_five_cards(combo_list)
        if score > best_score:
            best_score = score
            best_hand = combo_list
    
    return sorted(best_hand, key=lambda c: c.get_rank_value(), reverse=True)


def _evaluate_five_cards(cards: List[Card]) -> Tuple[int, List[int]]:
    """Helper to evaluate exactly 5 cards and return comparable tuple."""
    if _is_royal_flush(cards):
        return (10, [14, 13, 12, 11, 10])
    
    straight_flush_result = _is_straight_flush(cards)
    if straight_flush_result:
        return (9, [straight_flush_result])
    
    quads_result = _is_quads(cards)
    if quads_result:
        return (8, quads_result)
    
    boat_result = _is_boat(cards)
    if boat_result:
        return (7, boat_result)
    
    flush_result = _is_flush(cards)
    if flush_result:
        return (6, flush_result)
    
    straight_result = _is_straight(cards)
    if straight_result:
        return (5, [straight_result])
    
    trips_result = _is_trips(cards)
    if trips_result:
        return (4, trips_result)
    
    two_pair_result = _is_two_pair(cards)
    if two_pair_result:
        return (3, two_pair_result)
    
    one_pair_result = _is_one_pair(cards)
    if one_pair_result:
        return (2, one_pair_result)
    
    high_card_result = _get_high_card(cards)
    return (1, high_card_result)


def _is_royal_flush(cards: List[Card]) -> bool:
    """Check if hand is a royal flush (A-K-Q-J-10 of same suit)."""
    if len(cards) != 5:
        return False
    
    if not _is_flush(cards):
        return False
    
    ranks = sorted([c.get_rank_value() for c in cards])
    return ranks == [10, 11, 12, 13, 14]


def _is_straight_flush(cards: List[Card]) -> int:
    """
    Check if hand is a straight flush.
    Returns the high card value if true, 0 otherwise.
    Handles ace-low straight flush (wheel: A-2-3-4-5).
    """
    if len(cards) != 5:
        return 0
    
    if not _is_flush(cards):
        return 0
    
    straight_high = _is_straight(cards)
    return straight_high


def _is_quads(cards: List[Card]) -> List[int]:
    """
    Check if hand is quads (four of a kind).
    Returns [quads_rank, kicker] if true, empty list otherwise.
    """
    if len(cards) != 5:
        return []
    
    rank_counts = Counter(c.get_rank_value() for c in cards)
    counts = rank_counts.most_common()
    
    if len(counts) == 2 and counts[0][1] == 4:
        quads = counts[0][0]
        kicker = counts[1][0]
        return [quads, kicker]
    
    return []


def _is_boat(cards: List[Card]) -> List[int]:
    """
    Check if hand is a boat (full house).
    Returns [trips_rank, pair_rank] if true, empty list otherwise.
    """
    if len(cards) != 5:
        return []
    
    rank_counts = Counter(c.get_rank_value() for c in cards)
    counts = rank_counts.most_common()
    
    if len(counts) == 2 and counts[0][1] == 3 and counts[1][1] == 2:
        trips = counts[0][0]
        pair = counts[1][0]
        return [trips, pair]
    
    return []


def _is_flush(cards: List[Card]) -> List[int]:
    """
    Check if hand is a flush.
    Returns sorted list of ranks (high to low) if true, empty list otherwise.
    """
    if len(cards) != 5:
        return []
    
    suits = [c.suit for c in cards]
    if len(set(suits)) != 1:
        return []
    
    ranks = sorted([c.get_rank_value() for c in cards], reverse=True)
    return ranks


def _is_straight(cards: List[Card]) -> int:
    """
    Check if hand is a straight.
    Returns the high card value if true, 0 otherwise.
    Handles ace-low straight (wheel: A-2-3-4-5, returns 5 as high).
    """
    if len(cards) != 5:
        return 0
    
    ranks = sorted([c.get_rank_value() for c in cards])
    
    # Check for regular straight
    if ranks == list(range(ranks[0], ranks[0] + 5)):
        return ranks[-1]
    
    # Check for ace-low straight (wheel: A-2-3-4-5)
    if ranks == [2, 3, 4, 5, 14]:
        return 5  # High card is 5 in ace-low straight
    
    return 0


def _is_trips(cards: List[Card]) -> List[int]:
    """
    Check if hand is trips (three of a kind).
    Returns [trips_rank, kicker1, kicker2] if true, empty list otherwise.
    """
    if len(cards) != 5:
        return []
    
    rank_counts = Counter(c.get_rank_value() for c in cards)
    counts = rank_counts.most_common()
    
    if len(counts) == 3 and counts[0][1] == 3:
        trips = counts[0][0]
        kickers = sorted([counts[1][0], counts[2][0]], reverse=True)
        return [trips] + kickers
    
    return []


def _is_two_pair(cards: List[Card]) -> List[int]:
    """
    Check if hand is two pair.
    Returns [high_pair, low_pair, kicker] if true, empty list otherwise.
    """
    if len(cards) != 5:
        return []
    
    rank_counts = Counter(c.get_rank_value() for c in cards)
    counts = rank_counts.most_common()
    
    if len(counts) == 3 and counts[0][1] == 2 and counts[1][1] == 2:
        pairs = sorted([counts[0][0], counts[1][0]], reverse=True)
        kicker = counts[2][0]
        return pairs + [kicker]
    
    return []


def _is_one_pair(cards: List[Card]) -> List[int]:
    """
    Check if hand is one pair.
    Returns [pair_rank, kicker1, kicker2, kicker3] if true, empty list otherwise.
    """
    if len(cards) != 5:
        return []
    
    rank_counts = Counter(c.get_rank_value() for c in cards)
    counts = rank_counts.most_common()
    
    if len(counts) == 4 and counts[0][1] == 2:
        pair = counts[0][0]
        kickers = sorted([counts[1][0], counts[2][0], counts[3][0]], reverse=True)
        return [pair] + kickers
    
    return []


def _get_high_card(cards: List[Card]) -> List[int]:
    """
    Get high card hand.
    Returns sorted list of ranks (high to low).
    """
    ranks = sorted([c.get_rank_value() for c in cards], reverse=True)
    return ranks


def _determine_trips_type(best_hand: List[Card], hole_cards: List[Card], all_cards: List[Card]) -> str:
    """
    Determine if trips is a 'set' (pocket pair + board card) or 'trips' (board pair + hole card).
    
    Args:
        best_hand: The best 5-card hand (should be trips)
        hole_cards: The 2 hole cards
        all_cards: All cards (hole + board)
    
    Returns:
        'set' if pocket pair + board card, 'trips' if board pair + hole card
    """
    from collections import Counter
    
    # Get the trips rank
    rank_counts = Counter(c.get_rank_value() for c in best_hand)
    trips_rank = None
    for rank, count in rank_counts.items():
        if count == 3:
            trips_rank = rank
            break
    
    if trips_rank is None:
        return 'trips'  # Fallback, shouldn't happen
    
    # Count how many of the trips rank are in hole cards
    hole_ranks = [c.get_rank_value() for c in hole_cards]
    trips_in_hole = hole_ranks.count(trips_rank)
    
    # Get board cards (all cards minus hole cards)
    board_cards = [c for c in all_cards if c not in hole_cards]
    board_ranks = [c.get_rank_value() for c in board_cards]
    trips_on_board = board_ranks.count(trips_rank)
    
    # Set: pocket pair (2 in hole) + 1 on board = 3 total
    # Trips: 2 on board + 1 in hole = 3 total
    if trips_in_hole == 2:
        return 'set'  # Pocket pair + board card
    elif trips_in_hole == 1 and trips_on_board == 2:
        return 'trips'  # Board pair + hole card
    else:
        # Edge case: could be 3 on board (board trips) or other combinations
        # For simplicity, if not clearly a set, call it trips
        return 'trips'


def manual_test():
    """
    Interactive manual testing function for hand evaluation.
    Allows you to input hole cards and runout to test hand ranking.
    Prevents duplicate cards from being entered.
    """
    print("=" * 60)
    print("Manual Hand Evaluation Test")
    print("=" * 60)
    print("\nEnter your cards in format: rank + suit letter")
    print("Examples: As, Kh, 2d, 10c, Qs")
    print("Format: rank (2-10, J, Q, K, A) + suit (S, H, D, C)")
    print("Note: Duplicate cards are not allowed")
    print()
    
    try:
        # Track all entered cards to prevent duplicates
        entered_cards = set()
        
        # Get hole cards
        print("HOLE CARDS (2 cards):")
        hole1 = None
        hole2 = None
        
        # Get first hole card
        while hole1 is None:
            hole1_str = input("  Hole card 1: ").strip()
            try:
                card = Card.from_string(hole1_str)
                if card in entered_cards:
                    print(f"    ❌ Error: {card} has already been entered. Please enter a different card.")
                    continue
                hole1 = card
                entered_cards.add(card)
                print(f"    ✓ Added: {card}")
            except ValueError as e:
                print(f"    ❌ Error: {e}. Please try again.")
        
        # Get second hole card
        while hole2 is None:
            hole2_str = input("  Hole card 2: ").strip()
            try:
                card = Card.from_string(hole2_str)
                if card in entered_cards:
                    print(f"    ❌ Error: {card} has already been entered. Please enter a different card.")
                    continue
                hole2 = card
                entered_cards.add(card)
                print(f"    ✓ Added: {card}")
            except ValueError as e:
                print(f"    ❌ Error: {e}. Please try again.")
        
        print(f"\n✓ Hole cards: {hole1}, {hole2}")
        
        # Get runout (community cards)
        print("\nRUNOUT (community cards, 3-5 cards):")
        print("  Enter cards one at a time, or press Enter when done")
        runout = []
        for i in range(5):
            card_str = input(f"  Community card {i+1} (or Enter to finish): ").strip()
            if not card_str:
                break
            try:
                card = Card.from_string(card_str)
                if card in entered_cards:
                    print(f"    ❌ Error: {card} has already been entered. Please enter a different card.")
                    continue
                runout.append(card)
                entered_cards.add(card)
                print(f"    ✓ Added: {card}")
            except ValueError as e:
                print(f"    ❌ Error: {e}. Please try again.")
        
        if len(runout) < 3:
            print(f"\n⚠ Warning: Only {len(runout)} community cards entered.")
            print("  Need at least 3 cards for a complete hand.")
            if len(runout) == 0:
                print("  Using only hole cards (will need at least 3 more cards).")
        
        # Combine all cards
        all_cards = [hole1, hole2] + runout
        print(f"\n✓ Total cards: {len(all_cards)}")
        print(f"  Cards: {', '.join(str(c) for c in all_cards)}")
        
        # Evaluate hand
        print("\n" + "=" * 60)
        print("HAND EVALUATION")
        print("=" * 60)
        
        if len(all_cards) < 5:
            print(f"⚠ Need at least 5 cards to rank a hand. You have {len(all_cards)}.")
            print("  Adding random cards or you can add more community cards.")
            return
        
        score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=[hole1, hole2])
        
        # Map score to hand name
        hand_names = {
            10: "Royal Flush",
            9: "Straight Flush",
            8: "Quads",
            7: "Boat",
            6: "Flush",
            5: "Straight",
            4: "Trips",
            3: "Two Pair",
            2: "One Pair",
            1: "High Card"
        }
        
        hand_name = hand_names.get(score, "Unknown")
        
        # Show set vs trips distinction if applicable
        if score == 4 and 'trips_type' in metadata:
            trips_type = metadata['trips_type']
            if trips_type == 'set':
                hand_name = f"{hand_name} (Set - Pocket Pair)"
            else:
                hand_name = f"{hand_name} (Board Pair)"
        
        # Show board chop if applicable
        if metadata.get('board_chop', False):
            print(f"\n⚠️  BOARD CHOP - Hole cards don't play!")
            print(f"   The board itself contains the best 5-card hand.")
            print(f"   All players will split (chop) the pot equally.")
            
            # Get the best hand from board
            from itertools import combinations
            best_hand = None
            best_score = (0, [])
            board_cards = [c for c in all_cards if c not in [hole1, hole2]]
            
            for combo in combinations(all_cards, 5):
                combo_list = list(combo)
                combo_score = _evaluate_five_cards(combo_list)
                if combo_score > best_score:
                    best_score = combo_score
                    best_hand = combo_list
            
            if best_hand:
                print(f"\nBest 5-card hand (from board): {', '.join(str(c) for c in sorted(best_hand, key=lambda c: c.get_rank_value(), reverse=True))}")
                print(f"Hole cards: {hole1}, {hole2} (do not play)")
        
        print(f"\nHand Rank: {hand_name} (Score: {score})")
        print(f"Tiebreakers: {tiebreakers}")
        
        # Show best 5-card hand if more than 5 cards and not a board chop
        if len(all_cards) > 5 and not metadata.get('board_chop', False):
            from itertools import combinations
            best_hand = None
            best_score = (0, [])
            
            for combo in combinations(all_cards, 5):
                combo_list = list(combo)
                combo_score = _evaluate_five_cards(combo_list)
                if combo_score > best_score:
                    best_score = combo_score
                    best_hand = combo_list
            
            if best_hand:
                print(f"\nBest 5-card hand: {', '.join(str(c) for c in sorted(best_hand, key=lambda c: c.get_rank_value(), reverse=True))}")
        
        print("\n" + "=" * 60)
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("Please check your card format and try again.")
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import unittest
    
    class TestHandRanking(unittest.TestCase):
        """Unit tests for hand ranking function."""
        
        def test_royal_flush(self):
            """Test royal flush detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ks'), Card.from_string('Qs'),
                Card.from_string('Js'), Card.from_string('10s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 10)
            self.assertEqual(tiebreakers, [14, 13, 12, 11, 10])
        
        def test_straight_flush(self):
            """Test straight flush detection."""
            # Regular straight flush
            cards = [
                Card.from_string('9s'), Card.from_string('8s'), Card.from_string('7s'),
                Card.from_string('6s'), Card.from_string('5s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 9)
            self.assertEqual(tiebreakers, [9])
            
            # Ace-low straight flush (wheel)
            cards = [
                Card.from_string('Ah'), Card.from_string('2h'), Card.from_string('3h'),
                Card.from_string('4h'), Card.from_string('5h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 9)
            self.assertEqual(tiebreakers, [5])
        
        def test_quads(self):
            """Test quads (four of a kind) detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ac'), Card.from_string('Ks')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 8)
            self.assertEqual(tiebreakers, [14, 13])
        
        def test_boat(self):
            """Test boat (full house) detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ks'), Card.from_string('Kh')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 7)
            self.assertEqual(tiebreakers, [14, 13])
        
        def test_flush(self):
            """Test flush detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ks'), Card.from_string('Qs'),
                Card.from_string('9s'), Card.from_string('2s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 6)
            self.assertEqual(tiebreakers, [14, 13, 12, 9, 2])
        
        def test_straight(self):
            """Test straight detection."""
            # Regular straight
            cards = [
                Card.from_string('9s'), Card.from_string('8h'), Card.from_string('7d'),
                Card.from_string('6c'), Card.from_string('5s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 5)
            self.assertEqual(tiebreakers, [9])
            
            # Ace-low straight (wheel)
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 5)
            self.assertEqual(tiebreakers, [5])
            
            # High straight (10-J-Q-K-A)
            cards = [
                Card.from_string('As'), Card.from_string('Kh'), Card.from_string('Qd'),
                Card.from_string('Jc'), Card.from_string('10s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 5)
            self.assertEqual(tiebreakers, [14])
        
        def test_trips(self):
            """Test trips (three of a kind) detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ks'), Card.from_string('Qs')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 4)
            self.assertEqual(tiebreakers, [14, 13, 12])
        
        def test_two_pair(self):
            """Test two pair detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ks'),
                Card.from_string('Kh'), Card.from_string('Qs')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 3)
            self.assertEqual(tiebreakers, [14, 13, 12])
        
        def test_one_pair(self):
            """Test one pair detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ks'),
                Card.from_string('Qh'), Card.from_string('Js')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 2)
            self.assertEqual(tiebreakers, [14, 13, 12, 11])
        
        def test_high_card(self):
            """Test high card detection."""
            cards = [
                Card.from_string('As'), Card.from_string('Ks'), Card.from_string('Qs'),
                Card.from_string('9h'), Card.from_string('2d')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 1)
            self.assertEqual(tiebreakers, [14, 13, 12, 9, 2])
        
        def test_seven_card_hand(self):
            """Test that function works with 7 cards (Texas Hold'em)."""
            cards = [
                Card.from_string('As'), Card.from_string('Ks'), Card.from_string('Qs'),
                Card.from_string('Js'), Card.from_string('10s'),  # Royal flush
                Card.from_string('9h'), Card.from_string('8h')    # Extra cards
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 10)
            self.assertEqual(tiebreakers, [14, 13, 12, 11, 10])
        
        def test_edge_case_wheel_straight_flush(self):
            """Test ace-low straight flush (wheel) edge case."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2h'), Card.from_string('3h'),
                Card.from_string('4h'), Card.from_string('5h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 9)
            self.assertEqual(tiebreakers, [5])
        
        def test_edge_case_wheel_straight(self):
            """Test ace-low straight (wheel) edge case."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 5)
            self.assertEqual(tiebreakers, [5])
        
        def test_edge_case_not_straight_with_ace(self):
            """Test that A-K-Q-J-9 is not a straight."""
            cards = [
                Card.from_string('As'), Card.from_string('Kh'), Card.from_string('Qd'),
                Card.from_string('Jc'), Card.from_string('9s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertNotEqual(score, 5)  # Should not be a straight
        
        def test_edge_case_boat_vs_trips(self):
            """Test that boat is correctly identified vs trips."""
            # Boat
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ks'), Card.from_string('Kh')
            ]
            score, _, _ = rank_hand(cards)
            self.assertEqual(score, 7)
            
            # Trips (not boat)
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ks'), Card.from_string('Qs')
            ]
            score, _, _ = rank_hand(cards)
            self.assertEqual(score, 4)
        
        def test_edge_case_flush_vs_straight_flush(self):
            """Test that straight flush is correctly identified vs flush."""
            # Straight flush
            cards = [
                Card.from_string('9s'), Card.from_string('8s'), Card.from_string('7s'),
                Card.from_string('6s'), Card.from_string('5s')
            ]
            score, _, _ = rank_hand(cards)
            self.assertEqual(score, 9)
            
            # Flush (not straight)
            cards = [
                Card.from_string('As'), Card.from_string('Ks'), Card.from_string('Qs'),
                Card.from_string('9s'), Card.from_string('2s')
            ]
            score, _, _ = rank_hand(cards)
            self.assertEqual(score, 6)
        
        def test_empty_hand_error(self):
            """Test that empty hand raises error."""
            with self.assertRaises(ValueError):
                rank_hand([])
        
        def test_insufficient_cards_error(self):
            """Test that less than 5 cards raises error."""
            cards = [Card.from_string('As'), Card.from_string('Ks')]
            with self.assertRaises(ValueError):
                rank_hand(cards)
        
        def test_tiebreaker_ordering(self):
            """Test that tiebreakers are correctly ordered."""
            # Two pair: A-A-K-K-Q should have tiebreakers [14, 13, 12]
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ks'),
                Card.from_string('Kh'), Card.from_string('Qs')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 3)
            self.assertEqual(tiebreakers, [14, 13, 12])
            
            # Two pair: K-K-Q-Q-A should have tiebreakers [13, 12, 14]
            cards = [
                Card.from_string('Ks'), Card.from_string('Kh'), Card.from_string('Qs'),
                Card.from_string('Qh'), Card.from_string('As')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 3)
            self.assertEqual(tiebreakers, [13, 12, 14])
        
        def test_duplicate_cards_error(self):
            """Test that duplicate cards raise an error."""
            # Duplicate in hand
            cards = [
                Card.from_string('As'), Card.from_string('As'), Card.from_string('Ks'),
                Card.from_string('Qs'), Card.from_string('Js')
            ]
            with self.assertRaises(ValueError) as context:
                rank_hand(cards)
            self.assertIn("Duplicate cards", str(context.exception))
            
            # Duplicate in 7-card hand
            cards = [
                Card.from_string('As'), Card.from_string('Kh'), Card.from_string('Qs'),
                Card.from_string('Js'), Card.from_string('10s'), Card.from_string('9h'),
                Card.from_string('As')  # Duplicate As
            ]
            with self.assertRaises(ValueError) as context:
                rank_hand(cards)
            self.assertIn("Duplicate cards", str(context.exception))
        
        def test_set_vs_trips(self):
            """Test that set vs trips can be differentiated."""
            # Set: Pocket pair (As, Ah) + board card (Ad) + 2 other board cards
            hole_cards = [Card.from_string('As'), Card.from_string('Ah')]
            board = [Card.from_string('Ad'), Card.from_string('Ks'), Card.from_string('Qs')]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 4)
            self.assertEqual(metadata.get('trips_type'), 'set')
            
            # Trips: Board pair (As, Ah) + hole card (Ad) + 2 other cards
            hole_cards = [Card.from_string('Ad'), Card.from_string('Ks')]
            board = [Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Qs')]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 4)
            self.assertEqual(metadata.get('trips_type'), 'trips')
            
            # Test without hole_cards parameter (should not have trips_type)
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ks'), Card.from_string('Qs')
            ]
            score, tiebreakers, metadata = rank_hand(cards)
            self.assertEqual(score, 4)
            self.assertNotIn('trips_type', metadata)
        
        def test_board_chop_straight(self):
            """Test board chop with straight on board."""
            # Pocket Kings on board with straight 2-3-4-5-6
            hole_cards = [Card.from_string('Ks'), Card.from_string('Kh')]
            board = [
                Card.from_string('2s'), Card.from_string('3h'), Card.from_string('4d'),
                Card.from_string('5c'), Card.from_string('6s')
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 5)  # Straight
            self.assertTrue(metadata.get('board_chop', False))
            self.assertFalse(metadata.get('hole_cards_play', True))
        
        def test_board_chop_straight_flush(self):
            """Test board chop with straight flush on board."""
            # Any hole cards on board with straight flush
            hole_cards = [Card.from_string('Ks'), Card.from_string('Kh')]
            board = [
                Card.from_string('2s'), Card.from_string('3s'), Card.from_string('4s'),
                Card.from_string('5s'), Card.from_string('6s')
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 9)  # Straight Flush
            self.assertTrue(metadata.get('board_chop', False))
            self.assertFalse(metadata.get('hole_cards_play', True))
        
        def test_board_chop_flush(self):
            """Test board chop with flush on board."""
            hole_cards = [Card.from_string('Kh'), Card.from_string('Kd')]
            board = [
                Card.from_string('2s'), Card.from_string('4s'), Card.from_string('6s'),
                Card.from_string('8s'), Card.from_string('10s')  # Flush, not a straight
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 6)  # Flush
            self.assertTrue(metadata.get('board_chop', False))
            self.assertFalse(metadata.get('hole_cards_play', True))
        
        def test_no_board_chop_when_hole_cards_play(self):
            """Test that board chop is False when hole cards are used."""
            # Pocket Aces with board that doesn't make best hand (no straight/flush)
            hole_cards = [Card.from_string('As'), Card.from_string('Ah')]
            board = [
                Card.from_string('2h'), Card.from_string('3d'), Card.from_string('4c'),
                Card.from_string('6s'), Card.from_string('8h')  # No straight possible, mixed suits
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 2)  # One Pair (Aces)
            self.assertFalse(metadata.get('board_chop', True))
            self.assertTrue(metadata.get('hole_cards_play', False))
        
        def test_board_chop_with_quads_on_board(self):
            """Test board chop with quads on board where board kicker is highest."""
            # Board has quads with high kicker, hole cards are lower
            hole_cards = [Card.from_string('2s'), Card.from_string('3h')]
            board = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ac'), Card.from_string('Ks')  # K is higher than hole cards
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 8)  # Quads
            self.assertTrue(metadata.get('board_chop', False))
            self.assertFalse(metadata.get('hole_cards_play', True))
        
        def test_edge_case_wheel_straight_high_card(self):
            """Test that wheel (A-2-3-4-5) returns 5 as high card, not Ace."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 5)  # Straight
            self.assertEqual(tiebreakers, [5])  # High card is 5, not 14 (Ace)
        
        def test_edge_case_wheel_straight_flush_high_card(self):
            """Test that wheel straight flush returns 5 as high card."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2h'), Card.from_string('3h'),
                Card.from_string('4h'), Card.from_string('5h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 9)  # Straight Flush
            self.assertEqual(tiebreakers, [5])  # High card is 5
        
        def test_edge_case_wheel_vs_high_straight(self):
            """Test that high straight (10-J-Q-K-A) beats wheel."""
            wheel = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            high_straight = [
                Card.from_string('As'), Card.from_string('Kh'), Card.from_string('Qd'),
                Card.from_string('Jc'), Card.from_string('10s')
            ]
            
            wheel_score, wheel_tie, _ = rank_hand(wheel)
            high_score, high_tie, _ = rank_hand(high_straight)
            
            self.assertEqual(wheel_score, 5)
            self.assertEqual(high_score, 5)
            self.assertEqual(wheel_tie, [5])
            self.assertEqual(high_tie, [14])  # High straight wins with Ace high
            # High straight should beat wheel
            self.assertGreater(high_tie[0], wheel_tie[0])
        
        def test_edge_case_wheel_board_chop(self):
            """Test board chop with wheel on board."""
            hole_cards = [Card.from_string('Ks'), Card.from_string('Kh')]
            board = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 5)  # Straight (wheel)
            self.assertEqual(tiebreakers, [5])  # High card is 5
            self.assertTrue(metadata.get('board_chop', False))
            self.assertFalse(metadata.get('hole_cards_play', True))
        
        def test_edge_case_wheel_straight_flush_board_chop(self):
            """Test board chop with wheel straight flush on board."""
            hole_cards = [Card.from_string('Ks'), Card.from_string('Kh')]
            board = [
                Card.from_string('Ah'), Card.from_string('2h'), Card.from_string('3h'),
                Card.from_string('4h'), Card.from_string('5h')
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 9)  # Straight Flush (wheel)
            self.assertEqual(tiebreakers, [5])
            self.assertTrue(metadata.get('board_chop', False))
        
        def test_edge_case_not_straight_ace_high(self):
            """Test that A-K-Q-J-9 is not a straight (missing 10)."""
            cards = [
                Card.from_string('As'), Card.from_string('Kh'), Card.from_string('Qd'),
                Card.from_string('Jc'), Card.from_string('9s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertNotEqual(score, 5)  # Should not be a straight
            self.assertEqual(score, 1)  # Should be high card
        
        def test_edge_case_not_straight_ace_low(self):
            """Test that A-2-3-4-6 is not a straight (missing 5)."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('6h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertNotEqual(score, 5)  # Should not be a straight
            self.assertEqual(score, 1)  # Should be high card
        
        def test_edge_case_not_straight_middle_gap(self):
            """Test that 2-3-4-6-7 is not a straight (missing 5)."""
            cards = [
                Card.from_string('2s'), Card.from_string('3h'), Card.from_string('4d'),
                Card.from_string('6c'), Card.from_string('7s')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertNotEqual(score, 5)  # Should not be a straight
            self.assertEqual(score, 1)  # Should be high card
        
        def test_edge_case_quads_with_wheel_kicker(self):
            """Test quads with wheel kicker (edge case for tiebreakers)."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('Ac'), Card.from_string('5h')  # Wheel high card as kicker
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 8)  # Quads
            self.assertEqual(tiebreakers, [14, 5])  # Quads rank, kicker
        
        def test_edge_case_boat_with_wheel_trips(self):
            """Test full house where trips are wheel (A-A-A-2-2)."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'), Card.from_string('Ad'),
                Card.from_string('2s'), Card.from_string('2h')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 7)  # Boat
            self.assertEqual(tiebreakers, [14, 2])  # Trips rank, pair rank
        
        def test_edge_case_boat_with_wheel_pair(self):
            """Test full house where pair is wheel (A-A-2-2-2)."""
            cards = [
                Card.from_string('As'), Card.from_string('Ah'),
                Card.from_string('2s'), Card.from_string('2h'), Card.from_string('2d')
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 7)  # Boat
            self.assertEqual(tiebreakers, [2, 14])  # Trips rank (2), pair rank (A)
        
        def test_edge_case_wheel_in_seven_cards(self):
            """Test that wheel is correctly identified in 7-card hand."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h'),  # Wheel
                Card.from_string('Ks'), Card.from_string('Qh')  # Extra cards
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 5)  # Straight (wheel)
            self.assertEqual(tiebreakers, [5])
        
        def test_edge_case_wheel_straight_flush_in_seven_cards(self):
            """Test that wheel straight flush is correctly identified in 7-card hand."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2h'), Card.from_string('3h'),
                Card.from_string('4h'), Card.from_string('5h'),  # Wheel straight flush
                Card.from_string('Ks'), Card.from_string('Qh')  # Extra cards
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertEqual(score, 9)  # Straight Flush (wheel)
            self.assertEqual(tiebreakers, [5])
        
        def test_edge_case_high_straight_vs_wheel_in_seven_cards(self):
            """Test that high straight beats wheel when both possible in 7 cards."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h'),  # Wheel possible
                Card.from_string('Kh'), Card.from_string('Qh')   # High straight possible
            ]
            # Should choose high straight (10-J-Q-K-A) over wheel
            score, tiebreakers, _ = rank_hand(cards)
            # Actually, with these cards, we can't make high straight (need 10, J)
            # So it should be wheel
            self.assertEqual(score, 5)  # Straight
            # But let's test with actual high straight possible
            cards2 = [
                Card.from_string('As'), Card.from_string('Kh'), Card.from_string('Qd'),
                Card.from_string('Jc'), Card.from_string('10s'),  # High straight
                Card.from_string('2h'), Card.from_string('3h')    # Extra cards
            ]
            score2, tiebreakers2, _ = rank_hand(cards2)
            self.assertEqual(score2, 5)
            self.assertEqual(tiebreakers2, [14])  # High straight
        
        def test_edge_case_wheel_with_pocket_pair(self):
            """Test wheel with pocket pair (should still be wheel, not pair)."""
            hole_cards = [Card.from_string('Ks'), Card.from_string('Kh')]
            board = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            all_cards = hole_cards + board
            
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=hole_cards)
            self.assertEqual(score, 5)  # Straight (wheel), not pair
            self.assertEqual(tiebreakers, [5])
            self.assertTrue(metadata.get('board_chop', False))
        
        def test_edge_case_almost_wheel_missing_one(self):
            """Test A-2-3-4-X where X is not 5 (not a wheel)."""
            cards = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('6h')  # Missing 5
            ]
            score, tiebreakers, _ = rank_hand(cards)
            self.assertNotEqual(score, 5)  # Should not be a straight
            self.assertEqual(score, 1)  # High card
        
        def test_edge_case_wheel_vs_regular_straight_comparison(self):
            """Test that regular straight (6-7-8-9-10) beats wheel."""
            wheel = [
                Card.from_string('Ah'), Card.from_string('2s'), Card.from_string('3d'),
                Card.from_string('4c'), Card.from_string('5h')
            ]
            regular = [
                Card.from_string('6s'), Card.from_string('7h'), Card.from_string('8d'),
                Card.from_string('9c'), Card.from_string('10s')
            ]
            
            wheel_score, wheel_tie, _ = rank_hand(wheel)
            regular_score, regular_tie, _ = rank_hand(regular)
            
            self.assertEqual(wheel_score, 5)
            self.assertEqual(regular_score, 5)
            self.assertEqual(wheel_tie, [5])
            self.assertEqual(regular_tie, [10])
            # Regular straight should beat wheel
            self.assertGreater(regular_tie[0], wheel_tie[0])
    
    import sys
    
    # Check if user wants manual testing
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        manual_test()
    else:
        # Default: run unit tests
        unittest.main()
