"""
Poker decision-making engine (brain) for preflop play in heads-up scenarios.

Implements tight-aggressive (TAG) strategy with rule-based decision logic.
"""

from typing import Tuple, List
from card import Card, Rank, Suit


# Preflop hand rankings for heads-up (169 unique hands)
# Ranked from strongest (1) to weakest (169)
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
        # AA is top 0.6%, KK is top 1.2%, etc.
        pair_strength = {
            14: 1.00,  # AA - top 0.6%
            13: 0.94,  # KK - top 1.2%
            12: 0.88,  # QQ - top 1.8%
            11: 0.82,  # JJ - top 2.4%
            10: 0.76,  # TT - top 3.0%
            9: 0.70,   # 99 - top 3.6%
            8: 0.64,   # 88 - top 4.2%
            7: 0.58,   # 77 - top 4.8%
            6: 0.52,   # 66 - top 5.4%
            5: 0.46,   # 55 - top 6.0%
            4: 0.40,   # 44 - top 6.6%
            3: 0.35,   # 33 - top 7.2%
            2: 0.31,   # 22 - top 7.8%
        }
        return pair_strength[high_rank]
    
    # Suited hands are stronger than offsuit
    if is_suited:
        # Premium suited: AKs, AQs, AJs, KQs, etc.
        if high_rank == 14:  # Ace high
            suited_strength = {
                13: 0.88,  # AKs - top 12%
                12: 0.85,  # AQs - top 15%
                11: 0.82,  # AJs - top 18%
                10: 0.78,  # ATs - top 22%
                9: 0.74,   # A9s - top 26%
                8: 0.70,   # A8s - top 30%
                7: 0.66,   # A7s - top 34%
                6: 0.62,   # A6s - top 38%
                5: 0.58,   # A5s - top 42%
                4: 0.54,   # A4s - top 46%
                3: 0.50,   # A3s - top 50%
                2: 0.46,   # A2s - top 54%
            }
            return suited_strength[low_rank]
        
        # King high suited
        if high_rank == 13:
            suited_strength = {
                12: 0.80,  # KQs - top 20%
                11: 0.76,  # KJs - top 24%
                10: 0.72,  # KTs - top 28%
                9: 0.68,   # K9s - top 32%
                8: 0.64,   # K8s - top 36%
                7: 0.60,   # K7s - top 40%
                6: 0.56,   # K6s - top 44%
                5: 0.52,   # K5s - top 48%
                4: 0.48,   # K4s - top 52%
                3: 0.44,   # K3s - top 56%
                2: 0.40,   # K2s - top 60%
            }
            return suited_strength[low_rank]
        
        # Queen high suited
        if high_rank == 12:
            suited_strength = {
                11: 0.72,  # QJs - top 28%
                10: 0.68,  # QTs - top 32%
                9: 0.64,   # Q9s - top 36%
                8: 0.60,   # Q8s - top 40%
                7: 0.56,   # Q7s - top 44%
                6: 0.52,   # Q6s - top 48%
                5: 0.48,   # Q5s - top 52%
                4: 0.44,   # Q4s - top 56%
                3: 0.40,   # Q3s - top 60%
                2: 0.36,   # Q2s - top 64%
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
                13: 0.82,  # AKo - top 18%
                12: 0.78,  # AQo - top 22%
                11: 0.74,  # AJo - top 26%
                10: 0.70,  # ATo - top 30%
                9: 0.66,   # A9o - top 34%
                8: 0.62,   # A8o - top 38%
                7: 0.58,   # A7o - top 42%
                6: 0.54,   # A6o - top 46%
                5: 0.50,   # A5o - top 50%
                4: 0.46,   # A4o - top 54%
                3: 0.42,   # A3o - top 58%
                2: 0.38,   # A2o - top 62%
            }
            return offsuit_strength[low_rank]
        
        # King high offsuit
        if high_rank == 13:
            offsuit_strength = {
                12: 0.72,  # KQo - top 28%
                11: 0.68,  # KJo - top 32%
                10: 0.64,  # KTo - top 36%
                9: 0.60,   # K9o - top 40%
                8: 0.56,   # K8o - top 44%
                7: 0.52,   # K7o - top 48%
                6: 0.48,   # K6o - top 52%
                5: 0.44,   # K5o - top 56%
                4: 0.40,   # K4o - top 60%
                3: 0.36,   # K3o - top 64%
                2: 0.32,   # K2o - top 68%
            }
            return offsuit_strength.get(low_rank, 0.25)
        
        # Lower offsuit hands
        if high_rank >= 10:
            base = 0.50 - (high_rank - 10) * 0.08
            gap_penalty = (high_rank - low_rank - 1) * 0.05
            return max(0.10, base - gap_penalty)
        
        # Very low offsuit hands (like 72o)
        return max(0.05, 0.40 - (high_rank - 2) * 0.06)


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
    Make a preflop poker decision using tight-aggressive strategy.
    
    In heads-up poker:
    - Button (who is also Small Blind) acts FIRST preflop
    - Big Blind acts SECOND preflop (usually facing a raise)
    
    Args:
        hand: Tuple of two Card objects representing hole cards
        position: Position at table
                 - In heads-up: 0 = Big Blind, 1+ = Button (Small Blind)
        pot_odds: Pot odds ratio (optional, for future use)
        stack_depth: Effective stack size in big blinds (optional)
        big_blind: Big blind size (default 10.0)
        facing_raise: Whether player is facing a raise (True for BB when button raised)
        raise_amount: Amount of the raise to call (if facing_raise is True)
    
    Returns:
        Tuple of (action, bet_size) where:
        - action: "fold", "call", or "raise"
        - bet_size: Amount to bet (0 for fold, call amount, or raise amount)
    
    Strategy (Tight-Aggressive):
        Button (first to act):
        - Premium hands (top 15%): Always raise
        - Strong hands (15-35%): Raise
        - Medium hands (35-60%): Raise (aggressive)
        - Weak hands (bottom 40%): Sometimes raise as bluff, otherwise fold
        
        Big Blind (facing action):
        - Premium hands (top 15%): Call or raise
        - Strong hands (15-35%): Call
        - Medium hands (35-60%): Fold to raises
        - Weak hands (bottom 40%): Fold to raises
    
    Examples:
        >>> from card import Card, create_hand
        >>> hand = create_hand('As', 'Ks')
        >>> # Button acting first
        >>> make_decision(hand, position=1, big_blind=10)
        ('raise', 30.0)
        
        >>> # Big Blind facing a raise
        >>> make_decision(hand, position=0, big_blind=10, facing_raise=True, raise_amount=30)
        ('call', 30.0)
        
        >>> hand = create_hand('7h', '2d')
        >>> # Button acting first with weak hand
        >>> make_decision(hand, position=1, big_blind=10)
        ('fold', 0.0)
    """
    # Calculate hand strength percentile
    hand_strength = _calculate_preflop_strength(hand)
    
    # In heads-up: Button (position >= 1) acts FIRST, BB (position 0) acts SECOND
    is_button = position >= 1
    is_first_to_act = is_button  # Button acts first in heads-up
    
    # Determine action based on hand strength and position
    action = None
    bet_size = 0.0
    
    if is_first_to_act:
        # BUTTON (Small Blind) - Acting FIRST preflop
        # Can: fold, call (complete to BB), or raise
        
        # Premium hands (top 15%): Always raise
        if hand_strength >= 0.85:
            action = "raise"
            bet_size = 3.0 * big_blind
        
        # Strong hands (15-35%): Raise
        elif hand_strength >= 0.65:
            action = "raise"
            bet_size = 3.0 * big_blind
        
        # Medium hands (35-60%): Raise (aggressive from button)
        elif hand_strength >= 0.40:
            action = "raise"
            bet_size = 3.0 * big_blind
        
        # Weak hands (bottom 40%): Sometimes bluff, otherwise fold
        else:
            if hand_strength >= 0.25:
                # Medium-weak: Raise as bluff
                action = "raise"
                bet_size = 3.0 * big_blind
            else:
                # Very weak hands: Fold
                action = "fold"
                bet_size = 0.0
    
    else:
        # BIG BLIND - Acting SECOND, usually facing a raise
        # Can: fold, call (the raise), or re-raise
        
        if facing_raise:
            # Facing a raise from button
            call_amount = raise_amount if raise_amount else (3.0 * big_blind)
            
            # Premium hands (top 15%): Call or re-raise
            if hand_strength >= 0.85:
                # Re-raise with premium hands
                action = "raise"
                bet_size = 5.0 * big_blind  # 3-bet size
            
            # Strong hands (15-35%): Call
            elif hand_strength >= 0.65:
                action = "call"
                bet_size = call_amount
            
            # Medium hands (35-60%): Fold to raises
            elif hand_strength >= 0.40:
                action = "fold"
                bet_size = 0.0
            
            # Weak hands (bottom 40%): Fold to raises
            else:
                action = "fold"
                bet_size = 0.0
        else:
            # Not facing a raise (button folded or just called)
            # This is rare in heads-up, but handle it
            if hand_strength >= 0.65:
                # Strong enough to raise
                action = "raise"
                bet_size = 3.0 * big_blind
            else:
                # Check (which is effectively a call of 0 since BB already posted)
                action = "call"
                bet_size = 0.0
    
    return (action, bet_size)


def manual_test():
    """
    Interactive manual testing function for preflop decision making.
    Allows you to input hole cards, position, and see the decision.
    """
    print("=" * 60)
    print("Manual Preflop Decision Test")
    print("=" * 60)
    print("\nEnter your cards in format: rank + suit letter")
    print("Examples: As, Kh, 2d, 10c, Qs")
    print("Format: rank (2-10, J, Q, K, A) + suit (S, H, D, C)")
    print()
    
    try:
        # Get hole cards
        print("HOLE CARDS (2 cards):")
        hole1 = None
        hole2 = None
        
        # Get first hole card
        while hole1 is None:
            hole1_str = input("  Hole card 1: ").strip()
            try:
                card = Card.from_string(hole1_str)
                hole1 = card
                print(f"    ✓ Added: {card}")
            except ValueError as e:
                print(f"    ❌ Error: {e}. Please try again.")
        
        # Get second hole card
        while hole2 is None:
            hole2_str = input("  Hole card 2: ").strip()
            try:
                card = Card.from_string(hole2_str)
                if card == hole1:
                    print(f"    ❌ Error: {card} is the same as the first card. Please enter a different card.")
                    continue
                hole2 = card
                print(f"    ✓ Added: {card}")
            except ValueError as e:
                print(f"    ❌ Error: {e}. Please try again.")
        
        hand = (hole1, hole2)
        print(f"\n✓ Hand: {hole1}, {hole2}")
        
        # Get position
        print("\nPOSITION:")
        print("  In heads-up: 0 = Big Blind, 1+ = Button (Small Blind)")
        print("  Note: Button acts FIRST, Big Blind acts SECOND")
        position = None
        while position is None:
            pos_str = input("  Enter position (0 for BB, 1+ for Button): ").strip()
            try:
                position = int(pos_str)
                if position < 0:
                    print("    ❌ Error: Position must be >= 0. Please try again.")
                    position = None
                    continue
                pos_name = "Big Blind" if position == 0 else "Button (Small Blind)"
                print(f"    ✓ Position: {pos_name} ({position})")
            except ValueError:
                print("    ❌ Error: Please enter a valid number.")
        
        is_button = position >= 1
        
        # Get big blind size
        print("\nBIG BLIND SIZE:")
        big_blind = None
        while big_blind is None:
            bb_str = input("  Enter big blind size (default 10): ").strip()
            if not bb_str:
                big_blind = 10.0
                print(f"    ✓ Using default: ${big_blind:.2f}")
            else:
                try:
                    big_blind = float(bb_str)
                    if big_blind <= 0:
                        print("    ❌ Error: Big blind must be > 0. Please try again.")
                        big_blind = None
                        continue
                    print(f"    ✓ Big blind: ${big_blind:.2f}")
                except ValueError:
                    print("    ❌ Error: Please enter a valid number.")
        
        # Get facing_raise info (only for Big Blind)
        facing_raise = False
        raise_amount = None
        if not is_button:
            print("\nFACING ACTION:")
            print("  Are you facing a raise from the Button?")
            facing_str = input("  (y/n, default n): ").strip().lower()
            if facing_str in ['y', 'yes']:
                facing_raise = True
                print("    ✓ Facing a raise")
                # Get raise amount
                while raise_amount is None:
                    raise_str = input(f"  Enter raise amount (default {3.0 * big_blind:.2f}): ").strip()
                    if not raise_str:
                        raise_amount = 3.0 * big_blind
                        print(f"    ✓ Using default: ${raise_amount:.2f}")
                    else:
                        try:
                            raise_amount = float(raise_str)
                            if raise_amount <= big_blind:
                                print("    ❌ Error: Raise must be > big blind. Please try again.")
                                raise_amount = None
                                continue
                            print(f"    ✓ Raise amount: ${raise_amount:.2f}")
                        except ValueError:
                            print("    ❌ Error: Please enter a valid number.")
            else:
                print("    ✓ Not facing a raise (Button folded or just called)")
        
        # Calculate and display decision
        print("\n" + "=" * 60)
        print("DECISION ANALYSIS")
        print("=" * 60)
        
        strength = _calculate_preflop_strength(hand)
        action, bet_size = make_decision(
            hand, 
            position, 
            big_blind=big_blind,
            facing_raise=facing_raise,
            raise_amount=raise_amount
        )
        
        print(f"\nHand: {hole1}, {hole2}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"  → Top {(1-strength)*100:.1f}% of all starting hands")
        
        pos_name = "Big Blind" if position == 0 else "Button (Small Blind)"
        action_context = "First to act" if is_button else ("Facing raise" if facing_raise else "Not facing action")
        print(f"\nPosition: {pos_name} ({position})")
        print(f"Action Context: {action_context}")
        if facing_raise:
            print(f"  Raise to call: ${raise_amount:.2f}")
        
        print(f"\nStrategy Analysis:")
        if strength >= 0.85:
            category = "Premium (top 15%)"
        elif strength >= 0.65:
            category = "Strong (15-35%)"
        elif strength >= 0.40:
            category = "Medium (35-60%)"
        else:
            category = "Weak (bottom 40%)"
        print(f"  Category: {category}")
        
        print(f"\n" + "-" * 60)
        print(f"DECISION: {action.upper()}")
        if action == "raise":
            print(f"  Bet Size: ${bet_size:.2f} (3x big blind)")
        elif action == "call":
            print(f"  Bet Size: ${bet_size:.2f} (call big blind)")
        else:
            print(f"  Bet Size: ${bet_size:.2f} (fold)")
        print("-" * 60)
        
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


# Test function
if __name__ == "__main__":
    import sys
    from card import Card, create_hand
    
    # Check if user wants manual testing
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        manual_test()
    else:
        # Default: run automated tests
        print("=" * 60)
        print("Poker Brain - Preflop Decision Making Test")
        print("=" * 60)
        print("(Run with 'python3 brain.py manual' for interactive testing)")
        print()
        
        # Test case 1: AA (premium hand) on Button - should raise (first to act)
        print("Test 1: Pocket Aces (AA) on Button - First to Act")
        print("-" * 60)
        hand_aa = create_hand('As', 'Ah')
        action, bet_size = make_decision(hand_aa, position=1, big_blind=10)
        strength = _calculate_preflop_strength(hand_aa)
        print(f"Hand: {hand_aa[0]}, {hand_aa[1]}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"Position: Button (Small Blind) - First to act")
        print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
        assert action == "raise", f"Expected raise, got {action}"
        assert bet_size == 30.0, f"Expected $30, got ${bet_size}"
        print("✓ PASSED")
        print()
        
        # Test case 2: 72o (weakest hand) in BB facing a raise - should fold
        print("Test 2: 72o (weakest hand) in BB - Facing a Raise")
        print("-" * 60)
        hand_72o = create_hand('7h', '2d')
        action, bet_size = make_decision(hand_72o, position=0, big_blind=10, facing_raise=True, raise_amount=30)
        strength = _calculate_preflop_strength(hand_72o)
        print(f"Hand: {hand_72o[0]}, {hand_72o[1]}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"Position: Big Blind - Facing $30 raise")
        print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
        assert action == "fold", f"Expected fold, got {action}"
        assert bet_size == 0.0, f"Expected $0, got ${bet_size}"
        print("✓ PASSED")
        print()
        
        # Test case 3: AKs (example from user) on Button - should raise
        print("Test 3: AKs on Button - First to Act")
        print("-" * 60)
        hand_aks = create_hand('As', 'Ks')
        action, bet_size = make_decision(hand_aks, position=1, big_blind=10)
        strength = _calculate_preflop_strength(hand_aks)
        print(f"Hand: {hand_aks[0]}, {hand_aks[1]}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"Position: Button (Small Blind) - First to act")
        print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
        assert action == "raise", f"Expected raise, got {action}"
        assert bet_size == 30.0, f"Expected $30, got ${bet_size}"
        print("✓ PASSED")
        print()
        
        # Test case 4: AKs in BB facing a raise - should call or re-raise
        print("Test 4: AKs in BB - Facing a Raise")
        print("-" * 60)
        hand_aks = create_hand('As', 'Ks')
        action, bet_size = make_decision(hand_aks, position=0, big_blind=10, facing_raise=True, raise_amount=30)
        strength = _calculate_preflop_strength(hand_aks)
        print(f"Hand: {hand_aks[0]}, {hand_aks[1]}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"Position: Big Blind - Facing $30 raise")
        print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
        # Premium hand should re-raise
        assert action == "raise", f"Expected raise (re-raise), got {action}"
        assert bet_size == 50.0, f"Expected $50 (3-bet), got ${bet_size}"
        print("✓ PASSED")
        print()
        
        # Test case 5: Medium hand from button - should raise
        print("Test 5: Medium hand (K9o) from Button - First to Act")
        print("-" * 60)
        hand_k9o = create_hand('Kh', '9d')
        action, bet_size = make_decision(hand_k9o, position=1, big_blind=10)
        strength = _calculate_preflop_strength(hand_k9o)
        print(f"Hand: {hand_k9o[0]}, {hand_k9o[1]}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"Position: Button (Small Blind) - First to act")
        print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
        print("✓ Test completed")
        print()
        
        # Test case 6: Medium hand in BB facing a raise - should fold
        print("Test 6: Medium hand (K9o) in BB - Facing a Raise")
        print("-" * 60)
        hand_k9o = create_hand('Kh', '9d')
        action, bet_size = make_decision(hand_k9o, position=0, big_blind=10, facing_raise=True, raise_amount=30)
        strength = _calculate_preflop_strength(hand_k9o)
        print(f"Hand: {hand_k9o[0]}, {hand_k9o[1]}")
        print(f"Hand Strength: {strength:.2f} ({strength*100:.1f}th percentile)")
        print(f"Position: Big Blind - Facing $30 raise")
        print(f"Decision: {action.upper()}, Bet Size: ${bet_size:.2f}")
        assert action == "fold", f"Expected fold, got {action}"
        print("✓ PASSED")
        print()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
