"""
RL Brain wrapper - provides the same interface as brain.py but uses a trained DQN model.

This module is a drop-in replacement for brain.py in the simulation/game engine.
It loads a trained DQN checkpoint and converts game state observations into actions
using the learned Q-network.

Phase 3, Step 8: Model serving integration with existing engine.
"""

import os
import sys
import numpy as np
import torch
from typing import Tuple, List, Optional

# Ensure engine modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from card import Card
from strength import (
    calculate_preflop_strength,
    evaluate_postflop_hand,
)
from dqn import QNetwork


class RLBrain:
    """
    RL-powered brain that conforms to the brain.py interface.

    Provides make_preflop_decision() and make_postflop_decision()
    using a trained DQN model.
    """

    # Action mapping (matches PokerEnv)
    FOLD = 0
    CHECK_CALL = 1
    BET_THIRD = 2
    BET_TWO_THIRDS = 3
    BET_POT = 4
    ALL_IN = 5

    def __init__(
        self,
        checkpoint_path: str = None,
        device: str = "cpu",
        epsilon: float = 0.0,
    ):
        """
        Args:
            checkpoint_path: Path to DQN .pt checkpoint. If None, uses random policy.
            device: PyTorch device.
            epsilon: Exploration rate (0.0 for pure exploitation).
        """
        self.device = torch.device(device)
        self.epsilon = epsilon
        self.q_net = None

        if checkpoint_path and os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            self.q_net = QNetwork()
            self.q_net.load_state_dict(checkpoint["q_net"])
            self.q_net.eval()
            self.q_net.to(self.device)

        # Running opponent aggression stats (mimics env tracking)
        self._opp_actions = 0
        self._opp_aggressive = 0

        # Re-raise limiter to prevent infinite raise loops in simulation
        self._raise_count_this_street = 0
        self._max_raises_per_street = 3
        self._last_street = None

    def _build_observation(
        self,
        hand: Tuple[Card, Card],
        position: int,
        pot: float,
        current_stack: float,
        big_blind: float,
        facing_bet: bool,
        bet_amount: float,
        board: List[Card] = None,
        street: str = "preflop",
    ) -> np.ndarray:
        """Convert game state to 10-dim observation vector."""
        starting_stack = big_blind * 100  # Assume 100bb buy-in
        obs = np.zeros(10, dtype=np.float32)

        # [0] Hand strength
        if street == "preflop" or board is None or len(board) == 0:
            obs[0] = calculate_preflop_strength(hand)
        else:
            score, _, _ = evaluate_postflop_hand(hand, board)
            obs[0] = min(score / 10.0, 1.0)

        # [1] Position
        obs[1] = float(position)

        # [2] Pot normalized
        obs[2] = min(pot / (2 * starting_stack), 1.0)

        # [3] Stack depth
        obs[3] = min(current_stack / starting_stack, 1.0)

        # [4] Opponent aggression
        if self._opp_actions > 0:
            obs[4] = self._opp_aggressive / self._opp_actions
        else:
            obs[4] = 0.5

        # [5] Street
        street_map = {"preflop": 0.0, "flop": 0.33, "turn": 0.66, "river": 1.0}
        obs[5] = street_map.get(street, 0.0)

        # [6] Facing bet normalized
        call_amount = bet_amount if (facing_bet and bet_amount) else 0.0
        obs[6] = min(call_amount / starting_stack, 1.0)

        # Board texture
        if board and len(board) >= 3:
            board_ranks = [c.get_rank_value() for c in board]
            obs[7] = 1.0 if len(board_ranks) != len(set(board_ranks)) else 0.0

            suit_counts = {}
            for c in board:
                suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1
            obs[8] = 1.0 if max(suit_counts.values()) >= 3 else 0.0

            sorted_ranks = sorted(set(board_ranks))
            has_connected = False
            for i in range(len(sorted_ranks) - 2):
                if sorted_ranks[i + 2] - sorted_ranks[i] <= 4:
                    has_connected = True
                    break
            obs[9] = 1.0 if has_connected else 0.0

        return obs

    def _select_action(self, obs: np.ndarray) -> int:
        """Select action from Q-network or random."""
        if self.q_net is None or np.random.random() < self.epsilon:
            return np.random.randint(0, 6)

        with torch.no_grad():
            state_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
            q_values = self.q_net(state_t)
            return q_values.argmax(dim=1).item()

    def _action_to_game(
        self,
        action: int,
        pot: float,
        current_stack: float,
        big_blind: float,
        facing_bet: bool,
        bet_amount: float,
        current_bet: float = 0.0,
    ) -> Tuple[str, float]:
        """Convert discrete RL action to (action_str, bet_size) for the game engine."""

        if action == self.FOLD:
            if not facing_bet:
                return ("check", 0.0)  # Can't fold if not facing a bet
            return ("fold", 0.0)

        if action == self.CHECK_CALL:
            if facing_bet and bet_amount and bet_amount > 0:
                return ("call", bet_amount)
            return ("check", 0.0)

        # Cap re-raises to prevent infinite loops in simulation
        if self._raise_count_this_street >= self._max_raises_per_street:
            if facing_bet and bet_amount and bet_amount > 0:
                return ("call", bet_amount)
            return ("check", 0.0)

        # Betting actions
        if action == self.BET_THIRD:
            bet_size = pot * 0.33
        elif action == self.BET_TWO_THIRDS:
            bet_size = pot * 0.66
        elif action == self.BET_POT:
            bet_size = pot
        elif action == self.ALL_IN:
            self._raise_count_this_street += 1
            return ("raise", current_stack)
        else:
            bet_size = big_blind * 3  # Fallback

        # Ensure minimum raise
        min_raise = max(big_blind * 2, current_bet * 2)
        bet_size = max(bet_size, min_raise)
        bet_size = min(bet_size, current_stack)

        self._raise_count_this_street += 1
        return ("raise", bet_size)

    def get_action_probabilities(self, obs: np.ndarray) -> dict:
        """Get Q-values and action probabilities for visualization."""
        if self.q_net is None:
            return {"action_probs": [1/6]*6, "q_values": [0]*6, "confidence": 0.0}

        with torch.no_grad():
            state_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
            q_values = self.q_net(state_t).squeeze(0).cpu().numpy()

        # Softmax for probabilities
        exp_q = np.exp(q_values - q_values.max())
        probs = exp_q / exp_q.sum()

        action_names = ["fold", "check/call", "bet_0.33pot", "bet_0.66pot", "bet_1pot", "all-in"]
        best_action = int(np.argmax(q_values))

        return {
            "action": action_names[best_action],
            "action_probs": {name: round(float(p), 4) for name, p in zip(action_names, probs)},
            "q_values": [round(float(q), 4) for q in q_values],
            "confidence": round(float(probs[best_action]), 4),
        }

    # === brain.py compatible interface ===

    def make_preflop_decision(
        self,
        hand: Tuple[Card, Card],
        position: int,
        pot: float,
        current_stack: float,
        big_blind: float = 10.0,
        facing_raise: bool = False,
        raise_amount: float = None,
        facing_3bet: bool = False,
        facing_4bet: bool = False,
        is_first_to_act: bool = True,
    ) -> Tuple[str, float]:
        """brain.py-compatible preflop decision interface."""
        # Reset raise counter when entering a new street
        if self._last_street != "preflop":
            self._raise_count_this_street = 0
            self._last_street = "preflop"

        facing_bet = facing_raise
        bet_amount = raise_amount if facing_raise else 0.0

        # In heads-up preflop: Button/SB is "first to act" but must at least
        # call the BB. The simulation engine passes facing_raise=False and
        # is_first_to_act=True for this case. We need to recognize that we
        # must raise or call (fold = fold SB), never check.
        is_button_opening = (is_first_to_act and position == 1 and not facing_raise)

        obs = self._build_observation(
            hand=hand,
            position=position,
            pot=pot,
            current_stack=current_stack,
            big_blind=big_blind,
            facing_bet=facing_bet,
            bet_amount=bet_amount,
            board=None,
            street="preflop",
        )

        action = self._select_action(obs)
        current_bet = raise_amount if raise_amount else big_blind

        game_action, bet_size = self._action_to_game(
            action, pot, current_stack, big_blind,
            facing_bet, bet_amount, current_bet,
        )

        # Button opening: "check" is not valid, must raise or fold (which
        # the engine treats as completing the BB). Convert check -> call.
        if is_button_opening and game_action == "check":
            game_action = "call"
            bet_size = big_blind

        return (game_action, bet_size)

    def make_postflop_decision(
        self,
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
        street: str = "flop",
    ) -> Tuple[str, float]:
        """brain.py-compatible postflop decision interface."""
        # Reset raise counter when entering a new street
        if self._last_street != street:
            self._raise_count_this_street = 0
            self._last_street = street

        obs = self._build_observation(
            hand=hand,
            position=position,
            pot=pot,
            current_stack=current_stack,
            big_blind=big_blind,
            facing_bet=facing_bet,
            bet_amount=bet_amount if bet_amount else 0.0,
            board=board,
            street=street,
        )

        action = self._select_action(obs)
        current_bet = bet_amount if bet_amount else 0.0

        return self._action_to_game(
            action, pot, current_stack, big_blind,
            facing_bet, bet_amount if bet_amount else 0.0, current_bet,
        )
