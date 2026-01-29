#!/usr/bin/env python3
"""
RL Training entrypoint for the poker agent.

Supports:
  - DQN training (custom PyTorch)
  - PPO training (Stable-Baselines3)
  - Structured metrics emission to JSON (consumable by React frontend)
  - Model checkpointing
  - Reproducible seeding
  - Curriculum learning (Phase 4 Step 2)
  - Self-play / multi-agent (Phase 4 Step 2)

Usage:
  # DQN training (default)
  python train_rl.py --algo dqn --episodes 50000 --seed 42

  # PPO training
  python train_rl.py --algo ppo --timesteps 200000 --seed 42

  # Curriculum learning (easy -> hard opponents)
  python train_rl.py --algo dqn --episodes 50000 --curriculum

  # Self-play (agent plays against previous version of itself)
  python train_rl.py --algo dqn --episodes 50000 --self-play
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

import numpy as np
import torch


def train_dqn(args):
    """Train using custom DQN."""
    from poker_env import PokerEnv
    from dqn import DQNTrainer
    import fish_brain
    import brain as main_brain

    opponent = fish_brain if args.opponent == "fish" else main_brain

    env = PokerEnv(
        opponent_brain=opponent,
        small_blind=5.0,
        big_blind=10.0,
        starting_stack=1000.0,
        seed=args.seed,
        reward_mode=args.reward_mode,
    )

    trainer = DQNTrainer(
        env,
        lr=args.lr,
        gamma=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay,
        batch_size=args.batch_size,
        buffer_capacity=args.buffer_capacity,
        target_update_freq=args.target_update,
        seed=args.seed,
        checkpoint_dir=args.checkpoint_dir,
        metrics_path=args.metrics_path,
    )

    if args.resume:
        print(f"Resuming from checkpoint: {args.resume}")
        trainer.load_checkpoint(args.resume)

    print(f"Starting DQN training: {args.episodes} episodes")
    print(f"  Opponent: {args.opponent}")
    print(f"  Reward mode: {args.reward_mode}")
    print(f"  Seed: {args.seed}")
    print(f"  LR: {args.lr}, Gamma: {args.gamma}")
    print(f"  Epsilon: {args.epsilon_start} -> {args.epsilon_end} (decay {args.epsilon_decay})")
    print(f"  Metrics: {args.metrics_path}")
    print(f"  Checkpoints: {args.checkpoint_dir}")
    print()

    metrics = trainer.train(
        total_episodes=args.episodes,
        eval_interval=100,
        checkpoint_interval=max(1, args.episodes // 10),
        log_interval=args.log_interval,
    )

    print(f"\nTraining complete. {len(metrics)} metric points saved to {args.metrics_path}")
    return metrics


def train_ppo(args):
    """Train using Stable-Baselines3 PPO."""
    from poker_env import PokerEnv
    import fish_brain
    import brain as main_brain

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import BaseCallback
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        print("ERROR: stable-baselines3 not installed.")
        print("Install with: pip install stable-baselines3")
        sys.exit(1)

    opponent = fish_brain if args.opponent == "fish" else main_brain

    def make_env():
        return PokerEnv(
            opponent_brain=opponent,
            small_blind=5.0,
            big_blind=10.0,
            starting_stack=1000.0,
            seed=args.seed,
            reward_mode=args.reward_mode,
        )

    env = DummyVecEnv([make_env])

    # Metrics callback
    metrics_path = Path(args.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    class MetricsCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self.metrics_log = []
            self.episode_rewards = []
            self.hands_won = 0
            self.hands_played = 0
            self.start_time = time.time()

        def _on_step(self) -> bool:
            # Check for episode end
            infos = self.locals.get("infos", [])
            for info in infos:
                if "episode" in info:
                    ep_reward = info["episode"]["r"]
                    ep_length = info["episode"]["l"]
                    self.episode_rewards.append(ep_reward)
                    self.hands_played += 1
                    if ep_reward > 0:
                        self.hands_won += 1

            # Log every N steps
            if self.num_timesteps % (args.log_interval * 10) == 0 and self.hands_played > 0:
                avg_100 = np.mean(self.episode_rewards[-100:]) if self.episode_rewards else 0.0
                entry = {
                    "episode": self.hands_played,
                    "total_steps": self.num_timesteps,
                    "episode_reward": float(self.episode_rewards[-1]) if self.episode_rewards else 0.0,
                    "episode_length": 0,
                    "epsilon": 0.0,
                    "loss": 0.0,
                    "mean_q_value": 0.0,
                    "win_rate": round(self.hands_won / max(self.hands_played, 1), 4),
                    "avg_reward_100": round(float(avg_100), 4),
                    "hands_won": self.hands_won,
                    "hands_played": self.hands_played,
                    "timestamp": time.time(),
                    "wall_time_seconds": round(time.time() - self.start_time, 2),
                }

                # Try to get policy/value loss from logger
                if hasattr(self, "logger") and self.logger is not None:
                    try:
                        name_to_value = self.logger.name_to_value
                        entry["loss"] = round(float(name_to_value.get("train/loss", 0.0)), 6)
                    except Exception:
                        pass

                self.metrics_log.append(entry)
                self._save()

                if self.hands_played % 100 == 0:
                    print(
                        f"Step {self.num_timesteps} | "
                        f"Episodes: {self.hands_played} | "
                        f"Avg(100): {avg_100:.3f} | "
                        f"Win Rate: {self.hands_won/max(self.hands_played,1):.3f}"
                    )
            return True

        def _save(self):
            with open(metrics_path, "w") as f:
                json.dump(
                    {
                        "algorithm": "PPO",
                        "total_episodes": self.hands_played,
                        "metrics": self.metrics_log,
                    },
                    f,
                )

    callback = MetricsCallback()

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=args.lr,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=args.gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        verbose=0,
        seed=args.seed,
    )

    if args.resume:
        print(f"Loading PPO model from: {args.resume}")
        model = PPO.load(args.resume, env=env)

    print(f"Starting PPO training: {args.timesteps} timesteps")
    print(f"  Opponent: {args.opponent}")
    print(f"  Reward mode: {args.reward_mode}")
    print(f"  Seed: {args.seed}")
    print()

    model.learn(total_timesteps=args.timesteps, callback=callback)

    # Save final model
    save_path = checkpoint_dir / "ppo_final"
    model.save(str(save_path))
    print(f"\nPPO model saved to {save_path}")
    print(f"Metrics saved to {metrics_path}")

    return callback.metrics_log


def train_curriculum(args):
    """
    Curriculum learning: train against progressively harder opponents.

    Phase 4 Step 2 - Advanced RL Features.

    Schedule:
      Stage 1 (0-33%):   Train vs Fish (easy)
      Stage 2 (33-66%):  Train vs TAG (medium)
      Stage 3 (66-100%): Train vs self-play snapshot (hard)
    """
    from poker_env import PokerEnv
    from dqn import DQNTrainer
    import fish_brain
    import brain as main_brain

    total_episodes = args.episodes
    stage_episodes = total_episodes // 3

    metrics_path = Path(args.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    all_metrics = []

    print("=" * 60)
    print("CURRICULUM LEARNING")
    print("=" * 60)

    # Stage 1: vs Fish
    print(f"\n--- Stage 1: Training vs Fish ({stage_episodes} episodes) ---")
    env1 = PokerEnv(
        opponent_brain=fish_brain,
        seed=args.seed,
        reward_mode=args.reward_mode,
    )
    trainer = DQNTrainer(
        env1,
        lr=args.lr,
        gamma=args.gamma,
        epsilon_start=1.0,
        epsilon_end=0.1,
        epsilon_decay=args.epsilon_decay,
        seed=args.seed,
        checkpoint_dir=args.checkpoint_dir,
        metrics_path=str(metrics_path).replace(".json", "_stage1.json"),
    )
    stage1_metrics = trainer.train(
        total_episodes=stage_episodes,
        log_interval=args.log_interval,
        checkpoint_interval=max(1, stage_episodes // 5),
    )
    for m in stage1_metrics:
        m["curriculum_stage"] = 1
        m["opponent"] = "fish"
    all_metrics.extend(stage1_metrics)
    trainer.save_checkpoint("curriculum_stage1")

    # Stage 2: vs TAG
    print(f"\n--- Stage 2: Training vs TAG ({stage_episodes} episodes) ---")
    env2 = PokerEnv(
        opponent_brain=main_brain,
        seed=args.seed + 1,
        reward_mode=args.reward_mode,
    )
    trainer.env = env2
    trainer.epsilon = 0.5  # Partially explore again
    stage2_metrics = trainer.train(
        total_episodes=stage_episodes,
        log_interval=args.log_interval,
        checkpoint_interval=max(1, stage_episodes // 5),
    )
    for m in stage2_metrics:
        m["curriculum_stage"] = 2
        m["opponent"] = "tag"
    all_metrics.extend(stage2_metrics)
    trainer.save_checkpoint("curriculum_stage2")

    # Stage 3: Self-play
    print(f"\n--- Stage 3: Self-play ({stage_episodes} episodes) ---")
    from rl_brain import RLBrain
    self_play_brain = RLBrain(
        checkpoint_path=str(Path(args.checkpoint_dir) / "curriculum_stage2.pt"),
        device="cpu",
    )

    env3 = PokerEnv(
        opponent_brain=self_play_brain,
        seed=args.seed + 2,
        reward_mode=args.reward_mode,
    )
    trainer.env = env3
    trainer.epsilon = 0.3
    stage3_metrics = trainer.train(
        total_episodes=stage_episodes,
        log_interval=args.log_interval,
        checkpoint_interval=max(1, stage_episodes // 5),
    )
    for m in stage3_metrics:
        m["curriculum_stage"] = 3
        m["opponent"] = "self-play"
    all_metrics.extend(stage3_metrics)
    trainer.save_checkpoint("curriculum_final")

    # Save combined metrics
    with open(metrics_path, "w") as f:
        json.dump(
            {
                "algorithm": "DQN-Curriculum",
                "total_episodes": total_episodes,
                "stages": [
                    {"stage": 1, "opponent": "fish", "episodes": stage_episodes},
                    {"stage": 2, "opponent": "tag", "episodes": stage_episodes},
                    {"stage": 3, "opponent": "self-play", "episodes": stage_episodes},
                ],
                "metrics": all_metrics,
            },
            f,
        )

    print(f"\nCurriculum training complete. Metrics: {metrics_path}")
    return all_metrics


def train_self_play(args):
    """
    Multi-agent self-play training.

    Phase 4 Step 2 - The agent plays against snapshots of itself.
    Every N episodes, the opponent is updated to the current policy.
    """
    from poker_env import PokerEnv
    from dqn import DQNTrainer, QNetwork
    from rl_brain import RLBrain
    import fish_brain

    total_episodes = args.episodes
    snapshot_interval = max(1, total_episodes // 10)

    metrics_path = Path(args.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SELF-PLAY TRAINING")
    print("=" * 60)

    # Start with fish opponent for initial policy
    env = PokerEnv(
        opponent_brain=fish_brain,
        seed=args.seed,
        reward_mode=args.reward_mode,
    )

    trainer = DQNTrainer(
        env,
        lr=args.lr,
        gamma=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay,
        seed=args.seed,
        checkpoint_dir=args.checkpoint_dir,
        metrics_path=str(metrics_path),
    )

    all_metrics = []
    episodes_done = 0

    # Initial warmup vs fish
    warmup_episodes = min(5000, total_episodes // 5)
    print(f"\nWarmup: {warmup_episodes} episodes vs Fish")
    warmup_metrics = trainer.train(
        total_episodes=warmup_episodes,
        log_interval=args.log_interval,
        checkpoint_interval=max(1, warmup_episodes // 2),
    )
    for m in warmup_metrics:
        m["self_play_generation"] = 0
        m["opponent"] = "fish"
    all_metrics.extend(warmup_metrics)
    episodes_done += warmup_episodes

    # Self-play generations
    generation = 1
    remaining = total_episodes - warmup_episodes
    episodes_per_gen = max(1, remaining // 5)

    while episodes_done < total_episodes:
        # Save current model as opponent snapshot
        snapshot_path = checkpoint_dir / f"selfplay_gen{generation}.pt"
        trainer.save_checkpoint(f"selfplay_gen{generation}")

        # Create self-play opponent from snapshot
        self_brain = RLBrain(
            checkpoint_path=str(snapshot_path),
            device="cpu",
        )

        # New env with self-play opponent
        env = PokerEnv(
            opponent_brain=self_brain,
            seed=args.seed + generation,
            reward_mode=args.reward_mode,
        )
        trainer.env = env

        ep_this_gen = min(episodes_per_gen, total_episodes - episodes_done)
        print(f"\nGeneration {generation}: {ep_this_gen} episodes vs self (gen {generation-1})")

        gen_metrics = trainer.train(
            total_episodes=ep_this_gen,
            log_interval=args.log_interval,
            checkpoint_interval=max(1, ep_this_gen // 2),
        )
        for m in gen_metrics:
            m["self_play_generation"] = generation
            m["opponent"] = f"self-gen{generation-1}"
        all_metrics.extend(gen_metrics)

        episodes_done += ep_this_gen
        generation += 1

    trainer.save_checkpoint("selfplay_final")

    # Save all metrics
    with open(metrics_path, "w") as f:
        json.dump(
            {
                "algorithm": "DQN-SelfPlay",
                "total_episodes": total_episodes,
                "generations": generation,
                "metrics": all_metrics,
            },
            f,
        )

    print(f"\nSelf-play training complete. {generation} generations. Metrics: {metrics_path}")
    return all_metrics


def main():
    parser = argparse.ArgumentParser(description="Train RL poker agent")
    parser.add_argument("--algo", choices=["dqn", "ppo"], default="dqn", help="RL algorithm")
    parser.add_argument("--episodes", type=int, default=50000, help="Total training episodes (DQN)")
    parser.add_argument("--timesteps", type=int, default=200000, help="Total timesteps (PPO)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--buffer-capacity", type=int, default=50000, help="Replay buffer capacity")
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial epsilon")
    parser.add_argument("--epsilon-end", type=float, default=0.05, help="Final epsilon")
    parser.add_argument("--epsilon-decay", type=float, default=0.9995, help="Epsilon decay rate")
    parser.add_argument("--target-update", type=int, default=500, help="Target network update freq")
    parser.add_argument("--opponent", choices=["fish", "tag"], default="fish", help="Opponent type")
    parser.add_argument("--reward-mode", choices=["simple", "shaped", "normalized"], default="shaped")
    parser.add_argument("--checkpoint-dir", default="models/dqn", help="Checkpoint directory")
    parser.add_argument("--metrics-path", default="metrics/dqn_metrics.json", help="Metrics output path")
    parser.add_argument("--log-interval", type=int, default=10, help="Log every N episodes")
    parser.add_argument("--resume", type=str, default=None, help="Resume from checkpoint path")
    parser.add_argument("--curriculum", action="store_true", help="Use curriculum learning")
    parser.add_argument("--self-play", action="store_true", help="Use self-play training")

    args = parser.parse_args()

    # Adjust paths for PPO
    if args.algo == "ppo":
        if args.checkpoint_dir == "models/dqn":
            args.checkpoint_dir = "models/ppo"
        if args.metrics_path == "metrics/dqn_metrics.json":
            args.metrics_path = "metrics/ppo_metrics.json"

    # Create directories
    Path(args.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(args.metrics_path).parent.mkdir(parents=True, exist_ok=True)

    if args.curriculum:
        train_curriculum(args)
    elif args.self_play:
        train_self_play(args)
    elif args.algo == "dqn":
        train_dqn(args)
    elif args.algo == "ppo":
        train_ppo(args)


if __name__ == "__main__":
    main()
