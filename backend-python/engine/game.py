"""
Texas Hold'em Poker Game Engine (Heads-Up)

Implements a complete poker game simulator for heads-up (2-player) games.
Handles all betting rounds, pot management, showdowns, and game state.
"""

import random
from typing import List, Tuple, Dict
from card import Card, Rank, Suit
from hand_eval import rank_hand
from brain import make_decision, make_preflop_decision, make_postflop_decision


class Deck:
    """
    Standard 52-card deck for Texas Hold'em.
    Supports shuffling and dealing cards.
    """

    def __init__(self):
        """Initialize a fresh 52-card deck."""
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        """Reset deck to full 52 cards in order."""
        self.cards = []
        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            for rank in [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX,
                        Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK,
                        Rank.QUEEN, Rank.KING, Rank.ACE]:
                self.cards.append(Card(rank, suit))

    def shuffle(self):
        """Shuffle the deck randomly."""
        random.shuffle(self.cards)

    def deal(self, num_cards: int = 1) -> List[Card]:
        """
        Deal cards from the top of the deck.

        Args:
            num_cards: Number of cards to deal

        Returns:
            List of dealt cards

        Raises:
            ValueError: If not enough cards remaining
        """
        if len(self.cards) < num_cards:
            raise ValueError(f"Not enough cards in deck. Need {num_cards}, have {len(self.cards)}")

        dealt = []
        for _ in range(num_cards):
            dealt.append(self.cards.pop())
        return dealt

    def cards_remaining(self) -> int:
        """Return number of cards remaining in deck."""
        return len(self.cards)


class Player:
    """
    Represents a poker player in a heads-up game.
    """

    def __init__(self, name: str, stack: float, position: int):
        """
        Initialize a player.

        Args:
            name: Player name
            stack: Starting chip stack
            position: Position (0 = Big Blind, 1 = Button/Small Blind)
        """
        self.name = name
        self.stack = stack
        self.position = position
        self.hole_cards: List[Card] = []
        self.current_bet = 0.0
        self.total_invested = 0.0
        self.is_active = True  # Still in hand (hasn't folded)
        self.is_all_in = False

    def reset_for_new_hand(self):
        """Reset player state for a new hand."""
        self.hole_cards = []
        self.current_bet = 0.0
        self.total_invested = 0.0
        self.is_active = True
        self.is_all_in = False

    def post_blind(self, amount: float):
        """
        Post a blind bet.

        Args:
            amount: Blind amount to post
        """
        actual_bet = min(amount, self.stack)
        self.stack -= actual_bet
        self.current_bet = actual_bet
        self.total_invested += actual_bet

        if self.stack == 0:
            self.is_all_in = True

    def bet(self, amount: float) -> float:
        """
        Make a bet or raise.

        Args:
            amount: Amount to bet (total, not additional)

        Returns:
            Actual amount bet (may be less if all-in)
        """
        additional = amount - self.current_bet
        actual_additional = min(additional, self.stack)

        self.stack -= actual_additional
        self.current_bet += actual_additional
        self.total_invested += actual_additional

        if self.stack == 0:
            self.is_all_in = True

        return self.current_bet

    def fold(self):
        """Fold hand."""
        self.is_active = False

    def win_pot(self, amount: float):
        """Add winnings to stack."""
        self.stack += amount

    def __str__(self) -> str:
        """String representation of player."""
        status = "ACTIVE" if self.is_active else "FOLDED"
        if self.is_all_in:
            status = "ALL-IN"
        return f"{self.name} (Pos {self.position}): ${self.stack:.2f} [{status}]"


class PokerGame:
    """
    Texas Hold'em Heads-Up Poker Game Engine.

    Manages complete game flow from deal to showdown.
    Handles betting rounds, pot management, and winner determination.
    """

    def __init__(self, small_blind: float = 5.0, big_blind: float = 10.0):
        """
        Initialize poker game.

        Args:
            small_blind: Small blind amount
            big_blind: Big blind amount
        """
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.deck = Deck()
        self.players: List[Player] = []
        self.board: List[Card] = []
        self.pot = 0.0
        self.current_bet = 0.0
        self.game_phase = "preflop"  # preflop, flop, turn, river, showdown
        self.action_history: List[str] = []

    def add_player(self, name: str, stack: float, position: int) -> Player:
        """
        Add a player to the game.

        Args:
            name: Player name
            stack: Starting stack
            position: Position (0 = BB, 1 = Button/SB)

        Returns:
            Created Player object
        """
        player = Player(name, stack, position)
        self.players.append(player)
        return player

    def reset_for_new_hand(self):
        """Reset game state for a new hand."""
        self.deck.reset()
        self.deck.shuffle()
        self.board = []
        self.pot = 0.0
        self.current_bet = 0.0
        self.game_phase = "preflop"
        self.action_history = []

        for player in self.players:
            player.reset_for_new_hand()

    def post_blinds(self):
        """Post small blind and big blind."""
        if len(self.players) != 2:
            raise ValueError("Heads-up requires exactly 2 players")

        # In heads-up: Button is Small Blind (position 1), other is Big Blind (position 0)
        button = next(p for p in self.players if p.position == 1)
        bb = next(p for p in self.players if p.position == 0)

        # Post blinds (may be less if short-stacked)
        button.post_blind(self.small_blind)
        sb_posted = button.current_bet  # Actual amount posted

        bb.post_blind(self.big_blind)
        bb_posted = bb.current_bet  # Actual amount posted

        # Pot accumulates actual blinds posted
        self.pot = sb_posted + bb_posted
        self.current_bet = bb_posted

        self.action_history.append(f"{button.name} posts SB ${sb_posted:.2f}")
        self.action_history.append(f"{bb.name} posts BB ${bb_posted:.2f}")

    def deal_hole_cards(self):
        """Deal 2 hole cards to each player."""
        for player in self.players:
            player.hole_cards = self.deck.deal(2)
            self.action_history.append(f"Dealt to {player.name}: {player.hole_cards[0]}, {player.hole_cards[1]}")

    def deal_flop(self):
        """Deal the flop (3 community cards)."""
        self.deck.deal(1)  # Burn card
        self.board.extend(self.deck.deal(3))
        self.game_phase = "flop"
        self.action_history.append(f"FLOP: {self.board[0]}, {self.board[1]}, {self.board[2]}")

    def deal_turn(self):
        """Deal the turn (4th community card)."""
        self.deck.deal(1)  # Burn card
        self.board.append(self.deck.deal(1)[0])
        self.game_phase = "turn"
        self.action_history.append(f"TURN: {self.board[3]}")

    def deal_river(self):
        """Deal the river (5th community card)."""
        self.deck.deal(1)  # Burn card
        self.board.append(self.deck.deal(1)[0])
        self.game_phase = "river"
        self.action_history.append(f"RIVER: {self.board[4]}")

    def betting_round(self, phase: str) -> bool:
        """
        Execute a betting round.

        Args:
            phase: Game phase (preflop, flop, turn, river)

        Returns:
            True if hand should continue, False if someone folded
        """
        # Reset current bets for new betting round (except preflop where blinds are posted)
        if phase != "preflop":
            self.current_bet = 0.0
            for player in self.players:
                player.current_bet = 0.0

        # Determine action order
        # Preflop: Button acts first (position 1), BB acts second (position 0)
        # Postflop: BB acts first (position 0), Button acts second (position 1)
        if phase == "preflop":
            action_order = sorted([p for p in self.players if p.is_active and not p.is_all_in],
                                key=lambda p: p.position, reverse=True)
        else:
            action_order = sorted([p for p in self.players if p.is_active and not p.is_all_in],
                                key=lambda p: p.position)

        # If only one player can act, skip betting
        if len(action_order) <= 1:
            return True

        # Betting continues until all players have matched the current bet
        action_count = 0
        last_raiser = None

        while True:
            # Get current player
            current_player = action_order[action_count % len(action_order)]

            # Skip if current player is already all-in
            if current_player.is_all_in:
                action_count += 1
                # Prevent infinite loop
                if action_count > len(action_order) * 20:
                    break
                continue

            # Check if betting is complete
            all_matched = all(p.current_bet == self.current_bet or not p.is_active or p.is_all_in
                            for p in self.players)

            # If all bets matched and everyone has acted at least once, round is complete
            if all_matched and action_count >= len(action_order):
                # Special case: if someone raised, everyone must have a chance to act
                if last_raiser is None or action_count >= len(action_order) + action_order.index(last_raiser):
                    break

            # Count active non-all-in players
            active_players = [p for p in self.players if p.is_active and not p.is_all_in]

            # If everyone is all-in or folded (no one can act), stop
            if len(active_players) == 0:
                break

            # Player must act
            facing_raise = current_player.current_bet < self.current_bet
            facing_bet = facing_raise  # Alias for clarity
            raise_amount = self.current_bet if facing_raise else None
            bet_amount = self.current_bet - current_player.current_bet if facing_raise else None

            # Determine if player is in position (last to act)
            # In heads-up: Button acts last postflop (is in position)
            is_in_position = current_player.position == 1 if phase != "preflop" else False

            # Determine if player was preflop aggressor (last raiser preflop)
            # For now, assume button is preflop aggressor (simplified)
            is_preflop_aggressor = current_player.position == 1

            # Get action from brain based on phase/street
            if phase == "preflop":
                # Use preflop decision logic
                action, bet_size = make_preflop_decision(
                    hand=tuple(current_player.hole_cards),
                    position=current_player.position,
                    pot=self.pot,
                    current_stack=current_player.stack,
                    big_blind=self.big_blind,
                    facing_raise=facing_raise,
                    raise_amount=raise_amount,
                    facing_3bet=False,  # TODO: Track 3-bet/4-bet state
                    facing_4bet=False,
                    is_first_to_act=(current_player.position == 1)  # Button is first to act preflop
                )
            else:
                # Use postflop decision logic (flop, turn, river)
                action, bet_size = make_postflop_decision(
                    hand=tuple(current_player.hole_cards),
                    board=self.board,
                    position=current_player.position,
                    pot=self.pot,
                    current_stack=current_player.stack,
                    big_blind=self.big_blind,
                    is_in_position=is_in_position,
                    is_preflop_aggressor=is_preflop_aggressor,
                    facing_bet=facing_bet,
                    bet_amount=bet_amount,
                    street=phase  # Pass phase as street parameter
                )

            # Execute action
            if action == "fold":
                current_player.fold()
                self.action_history.append(f"{current_player.name} folds")
                return False  # Hand ends

            elif action == "call":
                # Call means matching the current bet
                call_amount = self.current_bet
                old_bet = current_player.current_bet
                actual_bet = current_player.bet(call_amount)
                additional = actual_bet - old_bet
                self.pot += additional

                if current_player.is_all_in:
                    self.action_history.append(f"{current_player.name} calls ${additional:.2f} (all-in)")
                else:
                    self.action_history.append(f"{current_player.name} calls ${additional:.2f}")

            elif action == "raise":
                # Ensure bet_size is at least current_bet + min raise
                raise_to = max(bet_size, self.current_bet * 2)
                old_bet = current_player.current_bet
                actual_bet = current_player.bet(raise_to)
                additional = actual_bet - old_bet
                self.pot += additional
                self.current_bet = actual_bet
                last_raiser = current_player

                if current_player.is_all_in:
                    self.action_history.append(f"{current_player.name} raises to ${actual_bet:.2f} (all-in)")
                else:
                    self.action_history.append(f"{current_player.name} raises to ${raise_to:.2f}")

            action_count += 1

            # Safety: prevent infinite loops
            if action_count > 100:
                raise RuntimeError("Betting round exceeded maximum actions")

        # Collect bets into pot
        for player in self.players:
            # Bets already added to pot during actions above
            player.current_bet = 0.0

        return True

    def showdown(self) -> Tuple[Player, str]:
        """
        Determine winner at showdown.

        Returns:
            Tuple of (winning_player, hand_description)
        """
        self.game_phase = "showdown"

        # Get active players
        active_players = [p for p in self.players if p.is_active]

        if len(active_players) == 1:
            # Only one player left (others folded)
            winner = active_players[0]
            return (winner, "opponent folded")

        # Evaluate hands
        best_player = None
        best_score = (0, [], {})

        hand_names = {
            10: "Royal Flush", 9: "Straight Flush", 8: "Quads",
            7: "Boat", 6: "Flush", 5: "Straight",
            4: "Trips", 3: "Two Pair", 2: "One Pair", 1: "High Card"
        }

        for player in active_players:
            all_cards = player.hole_cards + self.board
            score, tiebreakers, metadata = rank_hand(all_cards, hole_cards=player.hole_cards)

            # Add to action history
            hand_name = hand_names.get(score, "Unknown")
            if score == 4 and 'trips_type' in metadata:
                hand_name = f"{hand_name} ({metadata['trips_type']})"

            self.action_history.append(f"{player.name} shows {player.hole_cards[0]}, {player.hole_cards[1]}: {hand_name}")

            # Compare hands
            current_score = (score, tiebreakers)
            if best_player is None or current_score > best_score[:2]:
                best_player = player
                best_score = (score, tiebreakers, metadata)

        winner = best_player
        hand_description = hand_names.get(best_score[0], "Unknown")

        return (winner, hand_description)

    def award_pot(self, winner: Player):
        """Award pot to winner."""
        winner.win_pot(self.pot)
        self.action_history.append(f"{winner.name} wins ${self.pot:.2f}")
        self.pot = 0.0

    def play_hand(self) -> Tuple[Player, float, str]:
        """
        Play a complete hand from start to finish.

        Returns:
            Tuple of (winner, amount_won, hand_description)
        """
        self.reset_for_new_hand()

        # 1. Post blinds
        self.post_blinds()

        # 2. Deal hole cards
        self.deal_hole_cards()

        # 3. Preflop betting
        if not self.betting_round("preflop"):
            # Someone folded
            winner = next(p for p in self.players if p.is_active)
            amount_won = self.pot
            self.award_pot(winner)
            return (winner, amount_won, "opponent folded")

        # Check if both players are all-in (no more betting possible)
        both_all_in = all(p.is_all_in or not p.is_active for p in self.players)

        # 4. Flop
        if len([p for p in self.players if p.is_active]) > 1:
            self.deal_flop()

            if not both_all_in:
                if not self.betting_round("flop"):
                    winner = next(p for p in self.players if p.is_active)
                    amount_won = self.pot
                    self.award_pot(winner)
                    return (winner, amount_won, "opponent folded")

        # 5. Turn
        if len([p for p in self.players if p.is_active]) > 1:
            self.deal_turn()

            if not both_all_in:
                if not self.betting_round("turn"):
                    winner = next(p for p in self.players if p.is_active)
                    amount_won = self.pot
                    self.award_pot(winner)
                    return (winner, amount_won, "opponent folded")

        # 6. River
        if len([p for p in self.players if p.is_active]) > 1:
            self.deal_river()

            if not both_all_in:
                if not self.betting_round("river"):
                    winner = next(p for p in self.players if p.is_active)
                    amount_won = self.pot
                    self.award_pot(winner)
                    return (winner, amount_won, "opponent folded")

        # 7. Showdown
        winner, hand_desc = self.showdown()
        amount_won = self.pot
        self.award_pot(winner)

        return (winner, amount_won, hand_desc)

    def get_game_state(self) -> Dict:
        """
        Get current game state as a dictionary.

        Returns:
            Dictionary with game state information
        """
        return {
            "phase": self.game_phase,
            "pot": self.pot,
            "board": [str(c) for c in self.board],
            "current_bet": self.current_bet,
            "players": [
                {
                    "name": p.name,
                    "stack": p.stack,
                    "position": p.position,
                    "hole_cards": [str(c) for c in p.hole_cards] if p.hole_cards else [],
                    "current_bet": p.current_bet,
                    "is_active": p.is_active,
                    "is_all_in": p.is_all_in
                }
                for p in self.players
            ]
        }


def test_game():
    """Test the poker game engine."""
    print("=" * 60)
    print("Texas Hold'em Heads-Up Game Engine Test")
    print("=" * 60)
    print()

    # Test 1: Basic game setup
    print("Test 1: Basic Game Setup")
    print("-" * 60)
    game = PokerGame(small_blind=5.0, big_blind=10.0)
    player1 = game.add_player("Alice", 1000.0, 0)  # Big Blind
    player2 = game.add_player("Bob", 1000.0, 1)    # Button/Small Blind

    print(f"Players added:")
    print(f"  {player1}")
    print(f"  {player2}")
    assert len(game.players) == 2
    print("✓ PASSED")
    print()

    # Test 2: Deck operations
    print("Test 2: Deck Operations")
    print("-" * 60)
    deck = Deck()
    assert deck.cards_remaining() == 52, f"Expected 52 cards, got {deck.cards_remaining()}"
    print(f"New deck has {deck.cards_remaining()} cards")

    deck.shuffle()
    print("Deck shuffled")

    cards = deck.deal(5)
    assert len(cards) == 5, f"Expected 5 cards, got {len(cards)}"
    assert deck.cards_remaining() == 47, f"Expected 47 cards remaining, got {deck.cards_remaining()}"
    print(f"Dealt 5 cards: {', '.join(str(c) for c in cards)}")
    print(f"Cards remaining: {deck.cards_remaining()}")
    print("✓ PASSED")
    print()

    # Test 3: Play a complete hand
    print("Test 3: Play Complete Hand")
    print("-" * 60)
    game = PokerGame(small_blind=5.0, big_blind=10.0)
    player1 = game.add_player("Alice", 1000.0, 0)  # Big Blind
    player2 = game.add_player("Bob", 1000.0, 1)    # Button/Small Blind

    print("Starting stacks:")
    print(f"  Alice: ${player1.stack:.2f}")
    print(f"  Bob: ${player2.stack:.2f}")
    print()

    winner, amount_won, hand_desc = game.play_hand()

    print("Hand complete!")
    print(f"Winner: {winner.name}")
    print(f"Amount won: ${amount_won:.2f}")
    print(f"Winning hand: {hand_desc}")
    print()

    print("Final stacks:")
    for player in game.players:
        print(f"  {player.name}: ${player.stack:.2f}")

    # Verify conservation of chips (minus rake, which we don't have)
    total_chips = sum(p.stack for p in game.players)
    assert abs(total_chips - 2000.0) < 0.01, f"Chips not conserved: {total_chips}"
    print(f"Total chips: ${total_chips:.2f} (conserved ✓)")

    print("✓ PASSED")
    print()

    # Test 4: Action history
    print("Test 4: Action History")
    print("-" * 60)
    print("Hand history:")
    for i, action in enumerate(game.action_history, 1):
        print(f"  {i}. {action}")
    assert len(game.action_history) > 0, "No action history recorded"
    print("✓ PASSED")
    print()

    # Test 5: Multiple hands
    print("Test 5: Multiple Hands (10 hands)")
    print("-" * 60)
    game = PokerGame(small_blind=5.0, big_blind=10.0)
    player1 = game.add_player("Alice", 1000.0, 0)
    player2 = game.add_player("Bob", 1000.0, 1)

    wins = {"Alice": 0, "Bob": 0}

    for hand_num in range(10):
        winner, amount, desc = game.play_hand()
        wins[winner.name] += 1
        print(f"Hand {hand_num + 1}: {winner.name} wins ${amount:.2f} ({desc})")

        # Swap positions for next hand (button moves)
        player1.position, player2.position = player2.position, player1.position

    print()
    print(f"Results after 10 hands:")
    print(f"  Alice: {wins['Alice']} wins (${player1.stack:.2f})")
    print(f"  Bob: {wins['Bob']} wins (${player2.stack:.2f})")

    total_chips = player1.stack + player2.stack
    assert abs(total_chips - 2000.0) < 0.01, f"Chips not conserved: {total_chips}"
    print(f"  Total chips: ${total_chips:.2f} (conserved ✓)")
    print("✓ PASSED")
    print()

    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_game()
