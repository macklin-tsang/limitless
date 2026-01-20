"""
Poker Simulation Runner for Texas Hold'em Heads-Up Games.

This module provides functionality to:
- Run N games between specified agents
- Track results: wins, losses, profit/loss
- Save hand histories
- Calculate statistics: win rate, VPIP, hands won at showdown
- Export results to CSV for analysis
- Display progress for long simulations

Phase 1, Step 6 implementation.
"""

import csv
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Tuple, Callable, Optional
from card import Card, Rank, Suit
from hand_eval import rank_hand
import brain as tag_brain
import fish_brain


@dataclass
class AgentConfig:
    """Configuration for a poker agent."""
    name: str
    brain_module: object  # The brain module (brain or fish_brain)
    description: str = ""


@dataclass
class HandResult:
    """Result of a single hand."""
    hand_number: int
    winner_name: str
    amount_won: float
    win_description: str
    player1_cards: List[str]
    player2_cards: List[str]
    board: List[str]
    player1_stack_before: float
    player2_stack_before: float
    player1_stack_after: float
    player2_stack_after: float
    action_history: List[str]


@dataclass
class SimulationStats:
    """Statistics for an agent in a simulation."""
    agent_name: str
    games_played: int = 0
    hands_won: int = 0
    hands_lost: int = 0
    total_profit: float = 0.0
    showdowns_won: int = 0
    showdowns_total: int = 0
    hands_played_voluntarily: int = 0  # VPIP
    total_hands_dealt: int = 0

    @property
    def win_rate(self) -> float:
        """Win rate as percentage."""
        if self.total_hands_dealt == 0:
            return 0.0
        return (self.hands_won / self.total_hands_dealt) * 100

    @property
    def average_profit_per_hand(self) -> float:
        """Average profit per hand in big blinds."""
        if self.total_hands_dealt == 0:
            return 0.0
        return self.total_profit / self.total_hands_dealt

    @property
    def showdown_win_rate(self) -> float:
        """Win rate at showdown as percentage."""
        if self.showdowns_total == 0:
            return 0.0
        return (self.showdowns_won / self.showdowns_total) * 100

    @property
    def vpip(self) -> float:
        """Voluntarily Put money In Pot percentage."""
        if self.total_hands_dealt == 0:
            return 0.0
        return (self.hands_played_voluntarily / self.total_hands_dealt) * 100


@dataclass
class SimulationResult:
    """Complete result of a simulation run."""
    num_hands: int
    agent1_stats: SimulationStats
    agent2_stats: SimulationStats
    hand_results: List[HandResult] = field(default_factory=list)
    start_time: datetime = None
    end_time: datetime = None

    @property
    def duration_seconds(self) -> float:
        """Duration of simulation in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class SimulationDeck:
    """
    Deck for simulation with optional seeding for reproducibility.
    """

    def __init__(self, seed: int = None):
        """Initialize deck with optional random seed."""
        self.cards: List[Card] = []
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.reset()

    def reset(self):
        """Reset deck to full 52 cards."""
        self.cards = []
        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            for rank in [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX,
                        Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK,
                        Rank.QUEEN, Rank.KING, Rank.ACE]:
                self.cards.append(Card(rank, suit))

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, num_cards: int = 1) -> List[Card]:
        """Deal cards from the deck."""
        if len(self.cards) < num_cards:
            raise ValueError(f"Not enough cards in deck")
        dealt = []
        for _ in range(num_cards):
            dealt.append(self.cards.pop())
        return dealt


class SimulationPlayer:
    """Player for simulation with agent brain."""

    def __init__(self, name: str, stack: float, position: int, brain_module: object):
        self.name = name
        self.stack = stack
        self.position = position
        self.brain_module = brain_module
        self.hole_cards: List[Card] = []
        self.current_bet = 0.0
        self.total_invested = 0.0
        self.is_active = True
        self.is_all_in = False
        self.played_voluntarily = False

    def reset_for_new_hand(self):
        """Reset for new hand."""
        self.hole_cards = []
        self.current_bet = 0.0
        self.total_invested = 0.0
        self.is_active = True
        self.is_all_in = False
        self.played_voluntarily = False

    def post_blind(self, amount: float):
        """Post a blind bet."""
        actual_bet = min(amount, self.stack)
        self.stack -= actual_bet
        self.current_bet = actual_bet
        self.total_invested += actual_bet
        if self.stack == 0:
            self.is_all_in = True

    def bet(self, amount: float) -> float:
        """Make a bet or raise."""
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


class SimulationGame:
    """
    Poker game for simulation purposes.
    Uses agent brains for decision making.
    """

    def __init__(self, small_blind: float = 5.0, big_blind: float = 10.0, seed: int = None):
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.deck = SimulationDeck(seed)
        self.players: List[SimulationPlayer] = []
        self.board: List[Card] = []
        self.pot = 0.0
        self.current_bet = 0.0
        self.game_phase = "preflop"
        self.action_history: List[str] = []

    def add_player(self, name: str, stack: float, position: int, brain_module: object) -> SimulationPlayer:
        """Add a player with specified brain module."""
        player = SimulationPlayer(name, stack, position, brain_module)
        self.players.append(player)
        return player

    def reset_for_new_hand(self):
        """Reset game state for new hand."""
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
        """Post blinds."""
        button = next(p for p in self.players if p.position == 1)
        bb = next(p for p in self.players if p.position == 0)

        button.post_blind(self.small_blind)
        sb_posted = button.current_bet

        bb.post_blind(self.big_blind)
        bb_posted = bb.current_bet

        self.pot = sb_posted + bb_posted
        self.current_bet = bb_posted

        self.action_history.append(f"{button.name} posts SB ${sb_posted:.2f}")
        self.action_history.append(f"{bb.name} posts BB ${bb_posted:.2f}")

    def deal_hole_cards(self):
        """Deal hole cards to players."""
        for player in self.players:
            player.hole_cards = self.deck.deal(2)

    def deal_flop(self):
        """Deal the flop."""
        self.deck.deal(1)  # Burn
        self.board.extend(self.deck.deal(3))
        self.game_phase = "flop"
        self.action_history.append(f"FLOP: {', '.join(str(c) for c in self.board[:3])}")

    def deal_turn(self):
        """Deal the turn."""
        self.deck.deal(1)  # Burn
        self.board.append(self.deck.deal(1)[0])
        self.game_phase = "turn"
        self.action_history.append(f"TURN: {self.board[3]}")

    def deal_river(self):
        """Deal the river."""
        self.deck.deal(1)  # Burn
        self.board.append(self.deck.deal(1)[0])
        self.game_phase = "river"
        self.action_history.append(f"RIVER: {self.board[4]}")

    def betting_round(self, phase: str) -> bool:
        """Execute a betting round. Returns True if hand continues."""
        if phase != "preflop":
            self.current_bet = 0.0
            for player in self.players:
                player.current_bet = 0.0

        # Determine action order
        if phase == "preflop":
            action_order = sorted([p for p in self.players if p.is_active and not p.is_all_in],
                                key=lambda p: p.position, reverse=True)
        else:
            action_order = sorted([p for p in self.players if p.is_active and not p.is_all_in],
                                key=lambda p: p.position)

        if len(action_order) <= 1:
            return True

        action_count = 0
        last_raiser = None

        while True:
            current_player = action_order[action_count % len(action_order)]

            if current_player.is_all_in:
                action_count += 1
                if action_count > len(action_order) * 20:
                    break
                continue

            all_matched = all(p.current_bet == self.current_bet or not p.is_active or p.is_all_in
                            for p in self.players)

            if all_matched and action_count >= len(action_order):
                if last_raiser is None or action_count >= len(action_order) + action_order.index(last_raiser):
                    break

            active_players = [p for p in self.players if p.is_active and not p.is_all_in]
            if len(active_players) == 0:
                break

            # Get decision from agent's brain
            facing_raise = current_player.current_bet < self.current_bet
            facing_bet = facing_raise
            raise_amount = self.current_bet if facing_raise else None
            bet_amount = self.current_bet - current_player.current_bet if facing_raise else None
            is_in_position = current_player.position == 1 if phase != "preflop" else False
            is_preflop_aggressor = current_player.position == 1

            if phase == "preflop":
                # Special handling for heads-up preflop:
                # Button completing SB to BB should be treated as "first to act"
                is_button_completing = (current_player.position == 1 and
                                       current_player.current_bet == self.small_blind and
                                       self.current_bet == self.big_blind)

                if is_button_completing:
                    action, bet_size = current_player.brain_module.make_preflop_decision(
                        hand=tuple(current_player.hole_cards),
                        position=current_player.position,
                        pot=self.pot,
                        current_stack=current_player.stack,
                        big_blind=self.big_blind,
                        facing_raise=False,  # Treat as first to act
                        raise_amount=None,
                        facing_3bet=False,
                        facing_4bet=False,
                        is_first_to_act=True
                    )
                else:
                    action, bet_size = current_player.brain_module.make_preflop_decision(
                        hand=tuple(current_player.hole_cards),
                        position=current_player.position,
                        pot=self.pot,
                        current_stack=current_player.stack,
                        big_blind=self.big_blind,
                        facing_raise=facing_raise,
                        raise_amount=raise_amount,
                        facing_3bet=False,
                        facing_4bet=False,
                        is_first_to_act=False
                    )
            else:
                action, bet_size = current_player.brain_module.make_postflop_decision(
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
                    street=phase
                )

            # Track VPIP (any action other than fold/check when first to act preflop)
            if phase == "preflop" and action in ["call", "raise"]:
                current_player.played_voluntarily = True

            # Execute action
            if action == "fold":
                current_player.fold()
                self.action_history.append(f"{current_player.name} folds")
                return False

            elif action == "check":
                # Check means no additional bet
                self.action_history.append(f"{current_player.name} checks")

            elif action == "call":
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

            elif action == "check":
                self.action_history.append(f"{current_player.name} checks")

            action_count += 1
            if action_count > 100:
                raise RuntimeError("Betting round exceeded maximum actions")

        for player in self.players:
            player.current_bet = 0.0

        return True

    def showdown(self) -> Tuple[SimulationPlayer, str]:
        """Determine winner at showdown."""
        self.game_phase = "showdown"
        active_players = [p for p in self.players if p.is_active]

        if len(active_players) == 1:
            return (active_players[0], "opponent folded")

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

            hand_name = hand_names.get(score, "Unknown")
            self.action_history.append(f"{player.name} shows {player.hole_cards[0]}, {player.hole_cards[1]}: {hand_name}")

            current_score = (score, tiebreakers)
            if best_player is None or current_score > best_score[:2]:
                best_player = player
                best_score = (score, tiebreakers, metadata)

        hand_description = hand_names.get(best_score[0], "Unknown")
        return (best_player, hand_description)

    def award_pot(self, winner: SimulationPlayer):
        """Award pot to winner."""
        winner.win_pot(self.pot)
        self.action_history.append(f"{winner.name} wins ${self.pot:.2f}")
        self.pot = 0.0

    def play_hand(self) -> Tuple[SimulationPlayer, float, str, bool]:
        """
        Play a complete hand.

        Returns:
            Tuple of (winner, amount_won, hand_description, went_to_showdown)
        """
        self.reset_for_new_hand()
        self.post_blinds()
        self.deal_hole_cards()

        # Preflop
        if not self.betting_round("preflop"):
            winner = next(p for p in self.players if p.is_active)
            amount_won = self.pot
            self.award_pot(winner)
            return (winner, amount_won, "opponent folded", False)

        both_all_in = all(p.is_all_in or not p.is_active for p in self.players)

        # Flop
        if len([p for p in self.players if p.is_active]) > 1:
            self.deal_flop()
            if not both_all_in:
                if not self.betting_round("flop"):
                    winner = next(p for p in self.players if p.is_active)
                    amount_won = self.pot
                    self.award_pot(winner)
                    return (winner, amount_won, "opponent folded", False)

        # Turn
        if len([p for p in self.players if p.is_active]) > 1:
            self.deal_turn()
            if not both_all_in:
                if not self.betting_round("turn"):
                    winner = next(p for p in self.players if p.is_active)
                    amount_won = self.pot
                    self.award_pot(winner)
                    return (winner, amount_won, "opponent folded", False)

        # River
        if len([p for p in self.players if p.is_active]) > 1:
            self.deal_river()
            if not both_all_in:
                if not self.betting_round("river"):
                    winner = next(p for p in self.players if p.is_active)
                    amount_won = self.pot
                    self.award_pot(winner)
                    return (winner, amount_won, "opponent folded", False)

        # Showdown
        winner, hand_desc = self.showdown()
        amount_won = self.pot
        self.award_pot(winner)
        return (winner, amount_won, hand_desc, True)


def run_simulation(
    num_hands: int,
    agent1_config: AgentConfig,
    agent2_config: AgentConfig,
    starting_stack: float = 1000.0,
    small_blind: float = 5.0,
    big_blind: float = 10.0,
    seed: int = None,
    verbose: bool = False,
    show_progress: bool = True
) -> SimulationResult:
    """
    Run a simulation between two agents.

    Args:
        num_hands: Number of hands to play
        agent1_config: Configuration for agent 1
        agent2_config: Configuration for agent 2
        starting_stack: Starting stack for each player
        small_blind: Small blind amount
        big_blind: Big blind amount
        seed: Random seed for reproducibility
        verbose: Print detailed hand information
        show_progress: Show progress bar

    Returns:
        SimulationResult with statistics and hand histories
    """
    result = SimulationResult(
        num_hands=num_hands,
        agent1_stats=SimulationStats(agent_name=agent1_config.name),
        agent2_stats=SimulationStats(agent_name=agent2_config.name),
        start_time=datetime.now()
    )

    # Initialize game
    if seed is not None:
        random.seed(seed)

    game = SimulationGame(small_blind=small_blind, big_blind=big_blind, seed=seed)

    # Reset stacks to starting amount for each session
    player1_stack = starting_stack
    player2_stack = starting_stack

    # Progress tracking
    progress_interval = max(1, num_hands // 20)  # Update every 5%

    for hand_num in range(1, num_hands + 1):
        # Create fresh players for this hand with current stacks
        game.players = []
        position1 = (hand_num - 1) % 2  # Alternates 0, 1, 0, 1...
        position2 = 1 - position1

        p1 = game.add_player(agent1_config.name, player1_stack, position1, agent1_config.brain_module)
        p2 = game.add_player(agent2_config.name, player2_stack, position2, agent2_config.brain_module)

        # Store stacks before hand
        p1_stack_before = p1.stack
        p2_stack_before = p2.stack

        # Play the hand
        winner, amount_won, description, went_to_showdown = game.play_hand()

        # Update stacks
        player1_stack = p1.stack
        player2_stack = p2.stack

        # Record hand result
        hand_result = HandResult(
            hand_number=hand_num,
            winner_name=winner.name,
            amount_won=amount_won,
            win_description=description,
            player1_cards=[str(c) for c in p1.hole_cards] if p1.hole_cards else [],
            player2_cards=[str(c) for c in p2.hole_cards] if p2.hole_cards else [],
            board=[str(c) for c in game.board],
            player1_stack_before=p1_stack_before,
            player2_stack_before=p2_stack_before,
            player1_stack_after=p1.stack,
            player2_stack_after=p2.stack,
            action_history=game.action_history.copy()
        )
        result.hand_results.append(hand_result)

        # Update statistics
        result.agent1_stats.total_hands_dealt += 1
        result.agent2_stats.total_hands_dealt += 1

        if p1.played_voluntarily:
            result.agent1_stats.hands_played_voluntarily += 1
        if p2.played_voluntarily:
            result.agent2_stats.hands_played_voluntarily += 1

        if winner.name == agent1_config.name:
            result.agent1_stats.hands_won += 1
            result.agent1_stats.total_profit += (p1.stack - p1_stack_before)
            result.agent2_stats.hands_lost += 1
            result.agent2_stats.total_profit += (p2.stack - p2_stack_before)
        else:
            result.agent2_stats.hands_won += 1
            result.agent2_stats.total_profit += (p2.stack - p2_stack_before)
            result.agent1_stats.hands_lost += 1
            result.agent1_stats.total_profit += (p1.stack - p1_stack_before)

        if went_to_showdown:
            result.agent1_stats.showdowns_total += 1
            result.agent2_stats.showdowns_total += 1
            if winner.name == agent1_config.name:
                result.agent1_stats.showdowns_won += 1
            else:
                result.agent2_stats.showdowns_won += 1

        # Verbose output
        if verbose:
            print(f"Hand {hand_num}: {winner.name} wins ${amount_won:.2f} ({description})")
            print(f"  {agent1_config.name}: ${player1_stack:.2f}, {agent2_config.name}: ${player2_stack:.2f}")

        # Progress bar
        if show_progress and hand_num % progress_interval == 0:
            progress = hand_num / num_hands * 100
            bar_length = 30
            filled = int(bar_length * hand_num / num_hands)
            bar = '=' * filled + '-' * (bar_length - filled)
            print(f"\rProgress: [{bar}] {progress:.0f}% ({hand_num}/{num_hands})", end='', flush=True)

    if show_progress:
        print()  # New line after progress bar

    result.end_time = datetime.now()
    return result


def print_simulation_summary(result: SimulationResult):
    """Print a summary of simulation results."""
    print()
    print("=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    print()

    print(f"Hands played: {result.num_hands}")
    print(f"Duration: {result.duration_seconds:.2f} seconds")
    print(f"Hands/second: {result.num_hands / result.duration_seconds:.1f}" if result.duration_seconds > 0 else "")
    print()

    # Agent 1 stats
    s1 = result.agent1_stats
    print(f"{s1.agent_name}:")
    print(f"  Hands won: {s1.hands_won} ({s1.win_rate:.1f}%)")
    print(f"  Total profit: ${s1.total_profit:.2f}")
    print(f"  Avg profit/hand: ${s1.average_profit_per_hand:.2f}")
    print(f"  VPIP: {s1.vpip:.1f}%")
    print(f"  Showdown win rate: {s1.showdown_win_rate:.1f}% ({s1.showdowns_won}/{s1.showdowns_total})")
    print()

    # Agent 2 stats
    s2 = result.agent2_stats
    print(f"{s2.agent_name}:")
    print(f"  Hands won: {s2.hands_won} ({s2.win_rate:.1f}%)")
    print(f"  Total profit: ${s2.total_profit:.2f}")
    print(f"  Avg profit/hand: ${s2.average_profit_per_hand:.2f}")
    print(f"  VPIP: {s2.vpip:.1f}%")
    print(f"  Showdown win rate: {s2.showdown_win_rate:.1f}% ({s2.showdowns_won}/{s2.showdowns_total})")
    print()

    print("=" * 70)


def save_results_to_csv(result: SimulationResult, filename: str = None):
    """
    Save simulation results to CSV file.

    Args:
        result: SimulationResult to save
        filename: Output filename (default: simulation_results_TIMESTAMP.csv)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_results_{timestamp}.csv"

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow([
            'hand_number', 'winner', 'amount_won', 'description',
            'player1_cards', 'player2_cards', 'board',
            'player1_stack_before', 'player2_stack_before',
            'player1_stack_after', 'player2_stack_after'
        ])

        # Data rows
        for hr in result.hand_results:
            writer.writerow([
                hr.hand_number,
                hr.winner_name,
                hr.amount_won,
                hr.win_description,
                ' '.join(hr.player1_cards),
                ' '.join(hr.player2_cards),
                ' '.join(hr.board),
                hr.player1_stack_before,
                hr.player2_stack_before,
                hr.player1_stack_after,
                hr.player2_stack_after
            ])

    print(f"Results saved to {filename}")
    return filename


def save_hand_histories(result: SimulationResult, filename: str = None):
    """
    Save detailed hand histories to a text file.

    Args:
        result: SimulationResult to save
        filename: Output filename
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hand_histories_{timestamp}.txt"

    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("HAND HISTORIES\n")
        f.write("=" * 70 + "\n\n")

        for hr in result.hand_results:
            f.write(f"--- Hand #{hr.hand_number} ---\n")
            f.write(f"Winner: {hr.winner_name} (${hr.amount_won:.2f}) - {hr.win_description}\n")
            f.write(f"Player 1 cards: {' '.join(hr.player1_cards)}\n")
            f.write(f"Player 2 cards: {' '.join(hr.player2_cards)}\n")
            f.write(f"Board: {' '.join(hr.board)}\n")
            f.write(f"Stacks: P1 ${hr.player1_stack_before:.2f} -> ${hr.player1_stack_after:.2f}, ")
            f.write(f"P2 ${hr.player2_stack_before:.2f} -> ${hr.player2_stack_after:.2f}\n")
            f.write("Actions:\n")
            for action in hr.action_history:
                f.write(f"  {action}\n")
            f.write("\n")

    print(f"Hand histories saved to {filename}")
    return filename


# Pre-configured agents
TAG_AGENT = AgentConfig(
    name="TAG Bot",
    brain_module=tag_brain,
    description="Tight-Aggressive strategy - plays strong hands aggressively"
)

FISH_AGENT = AgentConfig(
    name="Fish",
    brain_module=fish_brain,
    description="Calling station - never folds preflop, always check-calls"
)


if __name__ == "__main__":
    print("=" * 70)
    print("Poker Simulation Runner")
    print("=" * 70)
    print()
    print("Running simulation: TAG Bot vs Fish")
    print("Hands: 100")
    print()

    # Run simulation
    result = run_simulation(
        num_hands=100,
        agent1_config=TAG_AGENT,
        agent2_config=FISH_AGENT,
        starting_stack=1000.0,
        small_blind=5.0,
        big_blind=10.0,
        seed=42,  # For reproducibility
        verbose=False,
        show_progress=True
    )

    # Print summary
    print_simulation_summary(result)

    # Save results
    save_results_to_csv(result)
    save_hand_histories(result)

    print()
    print("Simulation complete!")
