"""
Deep Q-Network (DQN) for poker agent.

Implements:
- Q-network (MLP: 10 -> 128 -> 64 -> 6)
- Target network for stable learning
- Experience replay buffer
- Epsilon-greedy exploration
- Training loop with structured metrics emission

Phase 3, Steps 3 & 5.
"""

import json
import os
import time
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class QNetwork(nn.Module):
    """Deep Q-Network: 10 inputs -> 128 -> 64 -> 6 outputs."""

    def __init__(self, state_dim: int = 10, action_dim: int = 6):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, action_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


@dataclass
class Transition:
    """Single experience tuple."""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """Fixed-size experience replay buffer."""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append(Transition(state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> List[Transition]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)


@dataclass
class TrainingMetrics:
    """Structured metrics for a training epoch/episode."""
    episode: int = 0
    total_steps: int = 0
    episode_reward: float = 0.0
    episode_length: int = 0
    epsilon: float = 1.0
    loss: float = 0.0
    mean_q_value: float = 0.0
    win_rate: float = 0.0
    avg_reward_100: float = 0.0
    hands_won: int = 0
    hands_played: int = 0
    timestamp: float = 0.0
    wall_time_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "episode": self.episode,
            "total_steps": self.total_steps,
            "episode_reward": round(self.episode_reward, 4),
            "episode_length": self.episode_length,
            "epsilon": round(self.epsilon, 4),
            "loss": round(self.loss, 6),
            "mean_q_value": round(self.mean_q_value, 4),
            "win_rate": round(self.win_rate, 4),
            "avg_reward_100": round(self.avg_reward_100, 4),
            "hands_won": self.hands_won,
            "hands_played": self.hands_played,
            "timestamp": self.timestamp,
            "wall_time_seconds": round(self.wall_time_seconds, 2),
        }


class DQNTrainer:
    """
    DQN training loop with:
    - Target network soft-update
    - Epsilon-greedy decay
    - Structured metrics logging to JSON
    - Model checkpointing
    """

    def __init__(
        self,
        env,
        *,
        lr: float = 1e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        buffer_capacity: int = 50000,
        target_update_freq: int = 500,
        tau: float = 0.005,
        seed: int = 42,
        checkpoint_dir: str = "models/dqn",
        metrics_path: str = "metrics/dqn_metrics.json",
        device: str = "auto",
    ):
        self.env = env
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.tau = tau
        self.seed = seed
        self.checkpoint_dir = Path(checkpoint_dir)
        self.metrics_path = Path(metrics_path)

        # Seeding
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        # Device
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Networks
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n
        self.q_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_capacity)

        # Metrics
        self.metrics_log: List[dict] = []
        self.episode_rewards: deque = deque(maxlen=100)
        self.total_steps = 0
        self.hands_won = 0
        self.hands_played = 0

        # Ensure dirs
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

    def select_action(self, state: np.ndarray) -> int:
        """Epsilon-greedy action selection."""
        if random.random() < self.epsilon:
            return self.env.action_space.sample()

        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_net(state_t)
            return q_values.argmax(dim=1).item()

    def update(self) -> Tuple[float, float]:
        """Sample batch and perform one gradient step. Returns (loss, mean_q)."""
        if len(self.buffer) < self.batch_size:
            return 0.0, 0.0

        batch = self.buffer.sample(self.batch_size)

        states = torch.FloatTensor(np.array([t.state for t in batch])).to(self.device)
        actions = torch.LongTensor([t.action for t in batch]).to(self.device)
        rewards = torch.FloatTensor([t.reward for t in batch]).to(self.device)
        next_states = torch.FloatTensor(np.array([t.next_state for t in batch])).to(self.device)
        dones = torch.FloatTensor([float(t.done) for t in batch]).to(self.device)

        # Current Q-values
        q_values = self.q_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Target Q-values (Double DQN: use online net to select, target net to evaluate)
        with torch.no_grad():
            next_actions = self.q_net(next_states).argmax(dim=1)
            next_q = self.target_net(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q = rewards + self.gamma * next_q * (1 - dones)

        loss = F.mse_loss(q_values, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.optimizer.step()

        return loss.item(), q_values.mean().item()

    def soft_update_target(self):
        """Soft-update target network parameters."""
        for tp, sp in zip(self.target_net.parameters(), self.q_net.parameters()):
            tp.data.copy_(self.tau * sp.data + (1.0 - self.tau) * tp.data)

    def train(
        self,
        total_episodes: int = 50000,
        eval_interval: int = 100,
        checkpoint_interval: int = 5000,
        log_interval: int = 10,
        callback=None,
    ) -> List[dict]:
        """
        Main training loop.

        Args:
            total_episodes: Total training episodes.
            eval_interval: Episodes between evaluation runs.
            checkpoint_interval: Episodes between model saves.
            log_interval: Episodes between metrics logging.
            callback: Optional callable(metrics_dict) for live streaming.

        Returns:
            List of metrics dicts.
        """
        start_time = time.time()
        best_avg_reward = -float("inf")

        for episode in range(1, total_episodes + 1):
            state, info = self.env.reset()
            episode_reward = 0.0
            episode_steps = 0
            done = False

            while not done:
                action = self.select_action(state)
                next_state, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated

                self.buffer.push(state, action, reward, next_state, done)
                state = next_state
                episode_reward += reward
                episode_steps += 1
                self.total_steps += 1

                # Train on batch
                loss, mean_q = self.update()

                # Soft-update target
                if self.total_steps % self.target_update_freq == 0:
                    self.soft_update_target()

            # Decay epsilon
            self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

            # Track win
            self.hands_played += 1
            if episode_reward > 0:
                self.hands_won += 1

            self.episode_rewards.append(episode_reward)
            avg_reward_100 = np.mean(self.episode_rewards) if self.episode_rewards else 0.0

            # Log metrics
            if episode % log_interval == 0:
                metrics = TrainingMetrics(
                    episode=episode,
                    total_steps=self.total_steps,
                    episode_reward=episode_reward,
                    episode_length=episode_steps,
                    epsilon=self.epsilon,
                    loss=loss,
                    mean_q_value=mean_q,
                    win_rate=self.hands_won / max(self.hands_played, 1),
                    avg_reward_100=avg_reward_100,
                    hands_won=self.hands_won,
                    hands_played=self.hands_played,
                    timestamp=time.time(),
                    wall_time_seconds=time.time() - start_time,
                )
                metrics_dict = metrics.to_dict()
                self.metrics_log.append(metrics_dict)
                self._save_metrics()

                if callback:
                    callback(metrics_dict)

            # Checkpoint
            if episode % checkpoint_interval == 0:
                self.save_checkpoint(f"dqn_ep{episode}")

                if avg_reward_100 > best_avg_reward:
                    best_avg_reward = avg_reward_100
                    self.save_checkpoint("dqn_best")

            # Progress
            if episode % eval_interval == 0:
                print(
                    f"Episode {episode}/{total_episodes} | "
                    f"Avg Reward(100): {avg_reward_100:.3f} | "
                    f"Epsilon: {self.epsilon:.3f} | "
                    f"Win Rate: {self.hands_won/max(self.hands_played,1):.3f} | "
                    f"Steps: {self.total_steps} | "
                    f"Buffer: {len(self.buffer)}"
                )

        # Final save
        self.save_checkpoint("dqn_final")
        self._save_metrics()
        return self.metrics_log

    def save_checkpoint(self, name: str):
        """Save model checkpoint."""
        path = self.checkpoint_dir / f"{name}.pt"
        torch.save(
            {
                "q_net": self.q_net.state_dict(),
                "target_net": self.target_net.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "total_steps": self.total_steps,
                "hands_won": self.hands_won,
                "hands_played": self.hands_played,
            },
            path,
        )

    def load_checkpoint(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.q_net.load_state_dict(checkpoint["q_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.epsilon = checkpoint.get("epsilon", self.epsilon_end)
        self.total_steps = checkpoint.get("total_steps", 0)
        self.hands_won = checkpoint.get("hands_won", 0)
        self.hands_played = checkpoint.get("hands_played", 0)

    def _save_metrics(self):
        """Persist metrics to JSON file."""
        with open(self.metrics_path, "w") as f:
            json.dump(
                {
                    "algorithm": "DQN",
                    "total_episodes": len(self.metrics_log) * 10 if self.metrics_log else 0,
                    "metrics": self.metrics_log,
                },
                f,
            )


def load_q_network(checkpoint_path: str, device: str = "cpu") -> QNetwork:
    """Load a trained Q-network for inference."""
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    net = QNetwork()
    net.load_state_dict(checkpoint["q_net"])
    net.eval()
    return net
