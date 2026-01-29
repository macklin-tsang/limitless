#!/usr/bin/env python3
"""
Evaluate trained RL agent against baseline opponents.

Runs systematic evaluation matches and produces structured results.

Usage:
  python evaluate_rl.py --checkpoint models/dqn/dqn_best.pt --games 1000
  python evaluate_rl.py --checkpoint models/dqn/dqn_best.pt --games 500 --opponent tag
  python evaluate_rl.py --checkpoint models/dqn/dqn_best.pt --all-opponents

Phase 3, Step 6.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

import numpy as np


def evaluate_agent(
    checkpoint_path: str,
    opponent_type: str,
    num_games: int = 1000,
    seed: int = 42,
    big_blind: float = 10.0,
) -> dict:
    """
    Evaluate RL agent vs a specific opponent.

    Returns metrics dict.
    """
    from simulation import run_simulation, AgentConfig
    from rl_brain import RLBrain
    import brain as main_brain
    import fish_brain

    # Create RL agent config
    rl_brain = RLBrain(checkpoint_path=checkpoint_path, device="cpu", epsilon=0.0)
    rl_config = AgentConfig(name="RL Agent", brain_module=rl_brain, description="Trained DQN agent")

    # Opponent config
    if opponent_type == "fish":
        opp_config = AgentConfig(name="Fish", brain_module=fish_brain, description="Calling Station")
    elif opponent_type == "tag":
        opp_config = AgentConfig(name="TAG Agent", brain_module=main_brain, description="Tight-Aggressive")
    elif opponent_type == "random":
        # Random agent: import rl_brain with high epsilon
        random_brain = RLBrain(checkpoint_path=None, device="cpu", epsilon=1.0)
        opp_config = AgentConfig(name="Random", brain_module=random_brain, description="Random actions")
    else:
        opp_config = AgentConfig(name="Fish", brain_module=fish_brain, description="Calling Station")

    starting_stack = big_blind * 100

    start_time = time.time()
    result = run_simulation(
        num_hands=num_games,
        agent1_config=rl_config,
        agent2_config=opp_config,
        starting_stack=starting_stack,
        small_blind=big_blind / 2,
        big_blind=big_blind,
        seed=seed,
        verbose=False,
        show_progress=True,
    )
    elapsed = time.time() - start_time

    # Compute metrics
    s1 = result.agent1_stats
    profits_bb = []
    for hr in result.hand_results:
        delta = hr.player1_stack_after - hr.player1_stack_before
        profits_bb.append(delta / big_blind)

    mean_profit = np.mean(profits_bb) if profits_bb else 0
    std_profit = np.std(profits_bb) if profits_bb else 0
    bb_per_100 = mean_profit * 100
    n = len(profits_bb)
    ci_margin = 1.96 * (std_profit / np.sqrt(max(n, 1))) * 100

    return {
        "opponent": opponent_type,
        "games": num_games,
        "win_rate": round(s1.win_rate, 2),
        "hands_won": s1.hands_won,
        "hands_lost": s1.hands_lost,
        "total_profit_bb": round(s1.total_profit / big_blind, 2),
        "bb_per_100": round(bb_per_100, 2),
        "std_dev_bb": round(std_profit, 4),
        "ci_low": round(bb_per_100 - ci_margin, 2),
        "ci_high": round(bb_per_100 + ci_margin, 2),
        "vpip": round(s1.vpip, 1),
        "showdown_win_rate": round(s1.showdown_win_rate, 1),
        "elapsed_seconds": round(elapsed, 2),
        "hands_per_second": round(num_games / elapsed, 1) if elapsed > 0 else 0,
    }


def evaluate_all_opponents(checkpoint_path: str, num_games: int = 1000, seed: int = 42):
    """Evaluate against all opponent types."""
    opponents = ["random", "fish", "tag"]
    results = []

    for opp in opponents:
        print(f"\n{'='*60}")
        print(f"Evaluating RL Agent vs {opp.upper()} ({num_games} games)")
        print(f"{'='*60}")

        metrics = evaluate_agent(checkpoint_path, opp, num_games, seed)
        results.append(metrics)

        print(f"  Win Rate: {metrics['win_rate']}%")
        print(f"  BB/100:   {metrics['bb_per_100']}")
        print(f"  95% CI:   [{metrics['ci_low']}, {metrics['ci_high']}]")
        print(f"  VPIP:     {metrics['vpip']}%")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate RL poker agent")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--games", type=int, default=1000, help="Number of games per evaluation")
    parser.add_argument("--opponent", type=str, default="fish", choices=["random", "fish", "tag"])
    parser.add_argument("--all-opponents", action="store_true", help="Evaluate against all opponents")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="metrics/eval_results.json", help="Output path")

    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    if args.all_opponents:
        results = evaluate_all_opponents(args.checkpoint, args.games, args.seed)
    else:
        results = [evaluate_agent(args.checkpoint, args.opponent, args.games, args.seed)]

    # Print summary table
    print(f"\n{'='*80}")
    print(f"{'Opponent':<10} {'Games':<8} {'Win%':<8} {'BB/100':<10} {'95% CI':<20} {'VPIP':<8}")
    print(f"{'-'*80}")
    for r in results:
        print(f"{r['opponent']:<10} {r['games']:<8} {r['win_rate']:<8} {r['bb_per_100']:<10} "
              f"[{r['ci_low']}, {r['ci_high']}]{'':<5} {r['vpip']:<8}")
    print(f"{'='*80}")

    # Save results
    with open(args.output, "w") as f:
        json.dump({
            "checkpoint": args.checkpoint,
            "evaluations": results,
        }, f, indent=2)

    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
