"""
Custom Gymnasium environment for heads-up Texas Hold'em poker.

Wraps the existing game engine to provide an RL-compatible interface.
Observation space: 10-dimensional continuous vector.
Action space: Discrete(6) - fold, check/call, bet_0.33pot, bet_0.66pot, bet_1pot, all-in.

Phase 3, Steps 1-2: Environment setup + reward shaping.
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Optional, Tuple, List
import random

from card import Card, Rank, Suit
from hand_eval import rank_hand
from strength import (
    calculate_preflop_strength,
    evaluate_postflop_hand,
    check_for_draws,
)


class PokerEnv(gym.Env):
    """
    Heads-up No-Limit Texas Hold'em environment.

    Observation (10-dim float32 in [0,1]):
        [0] hand_strength      - preflop percentile or postflop normalized score
        [1] position            - 0.0 = BB (OOP), 1.0 = Button (IP)
        [2] pot_size_norm       - pot / (2 * starting_stack)
        [3] stack_depth_norm    - current_stack / starting_stack
        [4] opponent_aggression - running aggression estimate
        [5] street              - 0.0=preflop, 0.33=flop, 0.66=turn, 1.0=river
        [6] facing_bet_norm     - amount to call / starting_stack  (0 if no bet)
        [7] board_paired        - 1.0 if board has a pair
        [8] flush_possible      - 1.0 if 3+ of one suit on board
        [9] straight_possible   - 1.0 if 3+ consecutive-ish ranks on board

    Actions:
        0 = fold
        1 = check / call
        2 = bet 0.33x pot
        3 = bet 0.66x pot
        4 = bet 1.0x pot
        5 = all-in
    """

    metadata = {"render_modes": ["human"]}

    # Action constants
    FOLD = 0
    CHECK_CALL = 1
    BET_THIRD = 2
    BET_TWO_THIRDS = 3
    BET_POT = 4
    ALL_IN = 5

    ACTION_NAMES = ["fold", "check/call", "bet_0.33pot", "bet_0.66pot", "bet_1pot", "all-in"]

    def __init__(
        self,
        opponent_brain=None,
        small_blind: float = 5.0,
        big_blind: float = 10.0,
        starting_stack: float = 1000.0,
        seed: Optional[int] = None,
        reward_mode: str = "shaped",
    ):
        """
        Args:
            opponent_brain: Module with make_preflop_decision / make_postflop_decision.
                           If None, uses the default rule-based brain.
            small_blind: Small blind amount.
            big_blind: Big blind amount.
            starting_stack: Starting stack for both players.
            seed: Random seed for reproducibility.
            reward_mode: 'simple' (terminal only), 'shaped' (intermediate signals),
                        'normalized' (scaled to [-1,1]).
        """
        super().__init__()

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(10,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(6)

        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_stack = starting_stack
        self.reward_mode = reward_mode

        # Lazy-import opponent brain to avoid circular imports
        if opponent_brain is None:
            import brain as default_brain
            self.opponent_brain = default_brain
        else:
            self.opponent_brain = opponent_brain

        self._seed = seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Game state
        self._deck_cards: List[Card] = []
        self._agent_cards: List[Card] = []
        self._opponent_cards: List[Card] = []
        self._board: List[Card] = []
        self._pot = 0.0
        self._agent_stack = starting_stack
        self._opponent_stack = starting_stack
        self._agent_bet = 0.0
        self._opponent_bet = 0.0
        self._agent_position = 1  # 1=Button(IP), 0=BB(OOP)
        self._street = "preflop"  # preflop, flop, turn, river
        self._done = False
        self._agent_folded = False
        self._opponent_folded = False
        self._agent_all_in = False
        self._opponent_all_in = False
        self._is_preflop_aggressor = False
        self._hand_number = 0

        # Opponent modeling running stats
        self._opp_actions_total = 0
        self._opp_aggressive_actions = 0

    def reset(self, *, seed=None, options=None):
        """Reset environment for a new hand."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self._hand_number += 1

        # Alternate positions each hand
        self._agent_position = self._hand_number % 2

        # Build and shuffle deck
        self._deck_cards = []
        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            for rank in [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX,
                         Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK,
                         Rank.QUEEN, Rank.KING, Rank.ACE]:
                self._deck_cards.append(Card(rank, suit))
        random.shuffle(self._deck_cards)

        # Deal hole cards
        self._agent_cards = [self._deck_cards.pop(), self._deck_cards.pop()]
        self._opponent_cards = [self._deck_cards.pop(), self._deck_cards.pop()]
        self._board = []

        # Post blinds
        self._agent_stack = self.starting_stack
        self._opponent_stack = self.starting_stack

        if self._agent_position == 1:
            # Agent is Button/SB
            sb_amt = min(self.small_blind, self._agent_stack)
            bb_amt = min(self.big_blind, self._opponent_stack)
            self._agent_stack -= sb_amt
            self._opponent_stack -= bb_amt
            self._agent_bet = sb_amt
            self._opponent_bet = bb_amt
        else:
            # Agent is BB
            sb_amt = min(self.small_blind, self._opponent_stack)
            bb_amt = min(self.big_blind, self._agent_stack)
            self._opponent_stack -= sb_amt
            self._agent_stack -= sb_amt  # wrong
            # Fix: agent posts BB
            self._agent_stack = self.starting_stack - bb_amt
            self._opponent_stack = self.starting_stack - sb_amt
            self._agent_bet = bb_amt
            self._opponent_bet = sb_amt

        self._pot = self._agent_bet + self._opponent_bet
        self._current_bet = max(self._agent_bet, self._opponent_bet)
        self._street = "preflop"
        self._done = False
        self._agent_folded = False
        self._opponent_folded = False
        self._agent_all_in = False
        self._opponent_all_in = False
        self._is_preflop_aggressor = False

        # Preflop: Button acts first in heads-up
        if self._agent_position == 1:
            # Agent is Button, acts first preflop -> we return obs, agent chooses
            pass
        else:
            # Agent is BB, opponent (Button) acts first preflop
            self._opponent_preflop_action()
            if self._opponent_folded:
                self._done = True
                obs = self._get_observation()
                return obs, self._get_info()

        obs = self._get_observation()
        return obs, self._get_info()

    def step(self, action: int):
        """
        Execute agent's action and advance game state.

        Returns:
            observation, reward, terminated, truncated, info
        """
        if self._done:
            return self._get_observation(), 0.0, True, False, self._get_info()

        reward = 0.0
        initial_stack = self._agent_stack + self._agent_bet

        # Execute agent action
        self._execute_agent_action(action)

        if self._agent_folded:
            # Agent folded
            self._done = True
            reward = self._calculate_reward("fold", initial_stack)
            return self._get_observation(), reward, True, False, self._get_info()

        if self._agent_all_in and self._opponent_all_in:
            # Both all-in, run out remaining streets
            reward = self._run_to_showdown(initial_stack)
            self._done = True
            return self._get_observation(), reward, True, False, self._get_info()

        # Opponent responds
        opp_folded = self._opponent_respond()

        if opp_folded:
            self._done = True
            reward = self._calculate_reward("opponent_folded", initial_stack)
            return self._get_observation(), reward, True, False, self._get_info()

        if self._agent_all_in or self._opponent_all_in:
            reward = self._run_to_showdown(initial_stack)
            self._done = True
            return self._get_observation(), reward, True, False, self._get_info()

        # Check if betting round is complete, advance street
        advanced = self._try_advance_street()

        if advanced and self._street == "showdown":
            reward = self._resolve_showdown(initial_stack)
            self._done = True
            return self._get_observation(), reward, True, False, self._get_info()

        if advanced and self._street != "preflop":
            # New street: if opponent acts first postflop (agent is IP)
            if self._agent_position == 1:
                # Opponent is OOP, acts first
                opp_folded = self._opponent_act_new_street()
                if opp_folded:
                    self._done = True
                    reward = self._calculate_reward("opponent_folded", initial_stack)
                    return self._get_observation(), reward, True, False, self._get_info()

        obs = self._get_observation()
        info = self._get_info()
        return obs, reward, self._done, False, info

    def _execute_agent_action(self, action: int):
        """Convert discrete action to game action."""
        if action == self.FOLD:
            self._agent_folded = True
            return

        if action == self.CHECK_CALL:
            # Call or check
            call_amount = self._current_bet - self._agent_bet
            if call_amount > 0:
                actual_call = min(call_amount, self._agent_stack)
                self._agent_stack -= actual_call
                self._agent_bet += actual_call
                self._pot += actual_call
                if self._agent_stack == 0:
                    self._agent_all_in = True
            # else: check (no money needed)
            return

        # Betting/raising actions
        if action == self.BET_THIRD:
            bet_size = self._pot * 0.33
        elif action == self.BET_TWO_THIRDS:
            bet_size = self._pot * 0.66
        elif action == self.BET_POT:
            bet_size = self._pot * 1.0
        elif action == self.ALL_IN:
            bet_size = self._agent_stack + self._agent_bet  # total
        else:
            bet_size = 0

        # Ensure minimum raise
        min_raise = self._current_bet * 2
        raise_to = max(bet_size + self._agent_bet, min_raise)

        if action == self.ALL_IN:
            raise_to = self._agent_stack + self._agent_bet

        additional = raise_to - self._agent_bet
        actual_additional = min(additional, self._agent_stack)

        self._agent_stack -= actual_additional
        self._agent_bet += actual_additional
        self._pot += actual_additional
        self._current_bet = self._agent_bet

        if self._agent_stack == 0:
            self._agent_all_in = True

        if self._street == "preflop":
            self._is_preflop_aggressor = True

    def _opponent_preflop_action(self):
        """Opponent acts first preflop (they are Button/SB)."""
        opp_hand = tuple(self._opponent_cards)
        facing_raise = self._opponent_bet < self._current_bet

        action, bet_size = self.opponent_brain.make_preflop_decision(
            hand=opp_hand,
            position=1,  # Opponent is Button
            pot=self._pot,
            current_stack=self._opponent_stack,
            big_blind=self.big_blind,
            facing_raise=False,
            raise_amount=None,
            facing_3bet=False,
            facing_4bet=False,
            is_first_to_act=True,
        )
        self._apply_opponent_action(action, bet_size)

    def _opponent_respond(self) -> bool:
        """Opponent responds to agent's action. Returns True if opponent folded."""
        opp_hand = tuple(self._opponent_cards)
        facing_bet = self._opponent_bet < self._current_bet
        bet_amount = self._current_bet - self._opponent_bet if facing_bet else None

        if self._street == "preflop":
            # Determine context
            action, bet_size = self.opponent_brain.make_preflop_decision(
                hand=opp_hand,
                position=1 - self._agent_position,
                pot=self._pot,
                current_stack=self._opponent_stack,
                big_blind=self.big_blind,
                facing_raise=facing_bet,
                raise_amount=self._current_bet if facing_bet else None,
                facing_3bet=False,
                facing_4bet=False,
                is_first_to_act=False,
            )
        else:
            is_ip = (1 - self._agent_position) == 1
            action, bet_size = self.opponent_brain.make_postflop_decision(
                hand=opp_hand,
                board=self._board,
                position=1 - self._agent_position,
                pot=self._pot,
                current_stack=self._opponent_stack,
                big_blind=self.big_blind,
                is_in_position=is_ip,
                is_preflop_aggressor=not self._is_preflop_aggressor,
                facing_bet=facing_bet,
                bet_amount=bet_amount,
                street=self._street,
            )

        self._track_opponent_action(action)
        return self._apply_opponent_action(action, bet_size)

    def _opponent_act_new_street(self) -> bool:
        """Opponent acts first on a new street (they are OOP)."""
        opp_hand = tuple(self._opponent_cards)
        is_ip = (1 - self._agent_position) == 1

        action, bet_size = self.opponent_brain.make_postflop_decision(
            hand=opp_hand,
            board=self._board,
            position=1 - self._agent_position,
            pot=self._pot,
            current_stack=self._opponent_stack,
            big_blind=self.big_blind,
            is_in_position=is_ip,
            is_preflop_aggressor=not self._is_preflop_aggressor,
            facing_bet=False,
            bet_amount=None,
            street=self._street,
        )

        self._track_opponent_action(action)
        return self._apply_opponent_action(action, bet_size)

    def _apply_opponent_action(self, action: str, bet_size: float) -> bool:
        """Apply opponent's action. Returns True if opponent folded."""
        if action == "fold":
            self._opponent_folded = True
            return True
        elif action == "check":
            pass
        elif action == "call":
            call_amount = self._current_bet - self._opponent_bet
            actual_call = min(call_amount, self._opponent_stack)
            self._opponent_stack -= actual_call
            self._opponent_bet += actual_call
            self._pot += actual_call
            if self._opponent_stack == 0:
                self._opponent_all_in = True
        elif action == "raise":
            raise_to = max(bet_size, self._current_bet * 2)
            additional = raise_to - self._opponent_bet
            actual_additional = min(additional, self._opponent_stack)
            self._opponent_stack -= actual_additional
            self._opponent_bet += actual_additional
            self._pot += actual_additional
            self._current_bet = self._opponent_bet
            if self._opponent_stack == 0:
                self._opponent_all_in = True
        return False

    def _track_opponent_action(self, action: str):
        """Track opponent actions for aggression estimate."""
        self._opp_actions_total += 1
        if action == "raise":
            self._opp_aggressive_actions += 1

    def _try_advance_street(self) -> bool:
        """Check if betting is complete and advance street. Returns True if advanced."""
        # Betting complete when both players have matched
        if self._agent_bet != self._opponent_bet:
            return False

        # Reset bets for new street
        self._agent_bet = 0.0
        self._opponent_bet = 0.0
        self._current_bet = 0.0

        if self._street == "preflop":
            self._deal_community(3)
            self._street = "flop"
        elif self._street == "flop":
            self._deal_community(1)
            self._street = "turn"
        elif self._street == "turn":
            self._deal_community(1)
            self._street = "river"
        elif self._street == "river":
            self._street = "showdown"

        return True

    def _deal_community(self, count: int):
        """Deal community cards (with burn)."""
        self._deck_cards.pop()  # Burn
        for _ in range(count):
            self._board.append(self._deck_cards.pop())

    def _run_to_showdown(self, initial_stack: float) -> float:
        """Run out remaining streets when someone is all-in."""
        streets_remaining = {
            "preflop": [3, 1, 1],
            "flop": [1, 1],
            "turn": [1],
            "river": [],
        }

        for count in streets_remaining.get(self._street, []):
            self._deal_community(count)

        self._street = "showdown"
        return self._resolve_showdown(initial_stack)

    def _resolve_showdown(self, initial_stack: float) -> float:
        """Compare hands and calculate reward."""
        agent_all = self._agent_cards + self._board
        opp_all = self._opponent_cards + self._board

        agent_score, agent_tb, _ = rank_hand(agent_all, hole_cards=self._agent_cards)
        opp_score, opp_tb, _ = rank_hand(opp_all, hole_cards=self._opponent_cards)

        agent_rank = (agent_score, agent_tb)
        opp_rank = (opp_score, opp_tb)

        if agent_rank > opp_rank:
            # Agent wins
            winnings = self._pot
            self._agent_stack += winnings
            return self._calculate_reward("won", initial_stack)
        elif agent_rank < opp_rank:
            # Opponent wins
            self._opponent_stack += self._pot
            return self._calculate_reward("lost", initial_stack)
        else:
            # Split pot
            half = self._pot / 2
            self._agent_stack += half
            self._opponent_stack += half
            return self._calculate_reward("split", initial_stack)

    def _calculate_reward(self, result: str, initial_stack: float) -> float:
        """
        Calculate reward based on result and reward mode.

        Reward modes:
        - 'simple': Only terminal chip delta normalized by big blind.
        - 'shaped': Terminal delta + intermediate shaping signals.
        - 'normalized': Shaped reward clamped to [-1, 1].
        """
        # Chip delta = final stack - what we started the hand with
        final_stack = self._agent_stack
        chip_delta = final_stack - initial_stack

        if self.reward_mode == "simple":
            return chip_delta / self.big_blind

        # Shaped rewards
        base_reward = chip_delta / self.big_blind

        if result == "fold":
            # Small penalty for folding to discourage over-folding
            base_reward -= 0.1
        elif result == "opponent_folded":
            # Bonus for winning without showdown
            base_reward += 0.3
        elif result == "won":
            # Extra for winning at showdown
            base_reward += 0.2
        elif result == "split":
            pass

        if self.reward_mode == "normalized":
            # Clamp to [-1, 1]
            max_bb = self.starting_stack / self.big_blind
            return np.clip(base_reward / max_bb, -1.0, 1.0)

        return base_reward

    def _get_observation(self) -> np.ndarray:
        """Build 10-dimensional observation vector."""
        obs = np.zeros(10, dtype=np.float32)

        # [0] Hand strength
        if self._street == "preflop":
            obs[0] = calculate_preflop_strength(tuple(self._agent_cards))
        else:
            score, _, meta = evaluate_postflop_hand(
                tuple(self._agent_cards), self._board
            )
            obs[0] = min(score / 10.0, 1.0)

        # [1] Position: 1.0 = Button (IP), 0.0 = BB (OOP)
        obs[1] = float(self._agent_position)

        # [2] Pot size normalized
        obs[2] = min(self._pot / (2 * self.starting_stack), 1.0)

        # [3] Stack depth normalized
        obs[3] = self._agent_stack / self.starting_stack

        # [4] Opponent aggression estimate
        if self._opp_actions_total > 0:
            obs[4] = self._opp_aggressive_actions / self._opp_actions_total
        else:
            obs[4] = 0.5

        # [5] Street encoding
        street_map = {"preflop": 0.0, "flop": 0.33, "turn": 0.66, "river": 1.0, "showdown": 1.0}
        obs[5] = street_map.get(self._street, 0.0)

        # [6] Facing bet normalized
        call_amount = max(0, self._current_bet - self._agent_bet)
        obs[6] = min(call_amount / self.starting_stack, 1.0)

        # Board texture features
        if len(self._board) >= 3:
            # [7] Board paired
            board_ranks = [c.get_rank_value() for c in self._board]
            obs[7] = 1.0 if len(board_ranks) != len(set(board_ranks)) else 0.0

            # [8] Flush possible (3+ of one suit)
            suit_counts = {}
            for c in self._board:
                suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1
            obs[8] = 1.0 if max(suit_counts.values()) >= 3 else 0.0

            # [9] Straight possible (3+ consecutive-ish)
            sorted_ranks = sorted(set(board_ranks))
            has_connected = False
            for i in range(len(sorted_ranks) - 2):
                if sorted_ranks[i + 2] - sorted_ranks[i] <= 4:
                    has_connected = True
                    break
            obs[9] = 1.0 if has_connected else 0.0

        return obs

    def _get_info(self) -> dict:
        """Return info dict for debugging."""
        return {
            "street": self._street,
            "pot": self._pot,
            "agent_stack": self._agent_stack,
            "opponent_stack": self._opponent_stack,
            "agent_position": self._agent_position,
            "hand_number": self._hand_number,
            "agent_cards": [str(c) for c in self._agent_cards],
            "board": [str(c) for c in self._board],
        }

    def render(self, mode="human"):
        """Render current state."""
        info = self._get_info()
        print(f"Hand #{info['hand_number']} | Street: {info['street']}")
        print(f"  Agent cards: {info['agent_cards']}")
        print(f"  Board: {info['board']}")
        print(f"  Pot: ${info['pot']:.2f}")
        print(f"  Agent stack: ${info['agent_stack']:.2f}")
        print(f"  Opponent stack: ${info['opponent_stack']:.2f}")
