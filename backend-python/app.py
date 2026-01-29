"""
Flask API wrapper for the Poker Engine.
Provides endpoints for running simulations, single hands, and RL training management.
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sys
import os
import math
import re
import json
import time
import threading
import subprocess
import signal
from pathlib import Path

# Add engine directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from simulation import (
    run_simulation,
    SimulationGame,
    AgentConfig,
    MAIN_AGENT,
    FISH_AGENT
)
import brain as main_brain
import fish_brain

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# RL agent loading (lazy - only when checkpoint exists)
_rl_brain_cache = {}

def _get_rl_brain(checkpoint_name="dqn_best"):
    """Lazily load an RL brain from checkpoint."""
    if checkpoint_name in _rl_brain_cache:
        return _rl_brain_cache[checkpoint_name]

    checkpoint_path = os.path.join(
        os.path.dirname(__file__), "models", "dqn", f"{checkpoint_name}.pt"
    )
    if not os.path.exists(checkpoint_path):
        return None

    try:
        from rl_brain import RLBrain
        brain = RLBrain(checkpoint_path=checkpoint_path, device="cpu", epsilon=0.0)
        _rl_brain_cache[checkpoint_name] = brain
        return brain
    except Exception as e:
        print(f"Failed to load RL brain: {e}")
        return None


# Agent configurations
AGENTS = {
    'TAG': AgentConfig(name='TAG Agent', brain_module=main_brain, description='Tight-Aggressive'),
    'FISH': AgentConfig(name='Fish', brain_module=fish_brain, description='Calling Station'),
    'MAIN': MAIN_AGENT,
}

# Try to register RL agent if checkpoint exists
_rl = _get_rl_brain("dqn_best")
if _rl:
    AGENTS['RL'] = AgentConfig(name='RL Agent', brain_module=_rl, description='Trained DQN Agent')

# Training process state
_training_process = None
_training_lock = threading.Lock()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'poker-engine'})


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Run a poker simulation between two agents.

    Request body:
    {
        "agent_type": "TAG",
        "opponent_type": "FISH",
        "num_games": 100,
        "small_blind": 5,
        "big_blind": 10
    }
    """
    data = request.get_json()

    agent_type = data.get('agent_type', 'TAG')
    opponent_type = data.get('opponent_type', 'FISH')
    num_games = min(int(data.get('num_games', 100)), 10000)  # Cap at 10000
    small_blind = float(data.get('small_blind', 5))
    big_blind = float(data.get('big_blind', 10))

    # Get agent configs
    agent1 = AGENTS.get(agent_type, MAIN_AGENT)
    agent2 = AGENTS.get(opponent_type, FISH_AGENT)

    # Buy-in is always 100bb regardless of stakes
    starting_stack = big_blind * 100

    # Run simulation
    result = run_simulation(
        num_hands=num_games,
        agent1_config=agent1,
        agent2_config=agent2,
        starting_stack=starting_stack,
        small_blind=small_blind,
        big_blind=big_blind,
        verbose=False,
        show_progress=False
    )

    # Return results
    return jsonify({
        'agentName': result.agent1_stats.agent_name,
        'opponentName': result.agent2_stats.agent_name,
        'wins': result.agent1_stats.hands_won,
        'losses': result.agent1_stats.hands_lost,
        'winRate': result.agent1_stats.win_rate / 100,  # Convert to decimal
        'totalProfit': result.agent1_stats.total_profit / big_blind,  # In BB
        'profitPerHand': result.agent1_stats.average_profit_per_hand / big_blind,  # In BB
        'handsPlayed': result.num_hands,
    })


@app.route('/api/simulate/single', methods=['POST'])
def simulate_single_hand():
    """
    Run a single hand between two agents and return full action history.

    Request body:
    {
        "agent1_type": "TAG",
        "agent2_type": "FISH",
        "small_blind": 5,
        "big_blind": 10,
        "starting_stack": 1000
    }
    """
    data = request.get_json()

    agent1_type = data.get('agent1_type', 'TAG')
    agent2_type = data.get('agent2_type', 'FISH')
    small_blind = float(data.get('small_blind', 5))
    big_blind = float(data.get('big_blind', 10))
    starting_stack = big_blind * 100  # Always 100bb buy-in

    # Get agent configs
    agent1_config = AGENTS.get(agent1_type, MAIN_AGENT)
    agent2_config = AGENTS.get(agent2_type, FISH_AGENT)

    # Create game
    game = SimulationGame(small_blind=small_blind, big_blind=big_blind)

    # Add players
    p1 = game.add_player(agent1_config.name, starting_stack, 1, agent1_config.brain_module)  # Button
    p2 = game.add_player(agent2_config.name, starting_stack, 0, agent2_config.brain_module)  # BB

    # Play hand
    winner, amount_won, description, went_to_showdown = game.play_hand()

    # Format cards for frontend
    def format_card(card):
        rank_map = {
            'TWO': '2', 'THREE': '3', 'FOUR': '4', 'FIVE': '5', 'SIX': '6',
            'SEVEN': '7', 'EIGHT': '8', 'NINE': '9', 'TEN': 'T',
            'JACK': 'J', 'QUEEN': 'Q', 'KING': 'K', 'ACE': 'A'
        }
        suit_map = {'HEARTS': 'h', 'DIAMONDS': 'd', 'CLUBS': 'c', 'SPADES': 's'}
        return {
            'rank': rank_map.get(card.rank.name, card.rank.name),
            'suit': suit_map.get(card.suit.name, card.suit.name.lower()[0])
        }

    return jsonify({
        'winner': winner.name,
        'amountWon': amount_won,
        'description': description,
        'wentToShowdown': went_to_showdown,
        'agent1': {
            'name': p1.name,
            'cards': [format_card(c) for c in p1.hole_cards] if p1.hole_cards else [],
            'stackBefore': starting_stack,
            'stackAfter': p1.stack,
        },
        'agent2': {
            'name': p2.name,
            'cards': [format_card(c) for c in p2.hole_cards] if p2.hole_cards else [],
            'stackBefore': starting_stack,
            'stackAfter': p2.stack,
        },
        'board': [format_card(c) for c in game.board],
        'pot': amount_won,
        'actionHistory': game.action_history,
    })


@app.route('/api/simulate/session', methods=['POST'])
def start_session():
    """
    Start a new session and run multiple hands, returning results for each.

    Request body:
    {
        "agent1_type": "TAG",
        "agent2_type": "FISH",
        "num_hands": 1,
        "small_blind": 5,
        "big_blind": 10,
        "starting_stack": 1000
    }
    """
    data = request.get_json()

    agent1_type = data.get('agent1_type', 'TAG')
    agent2_type = data.get('agent2_type', 'FISH')
    num_hands = min(int(data.get('num_hands', 1)), 100)  # Cap at 100 for session
    small_blind = float(data.get('small_blind', 5))
    big_blind = float(data.get('big_blind', 10))
    starting_stack = big_blind * 100  # Always 100bb buy-in

    # Get agent configs
    agent1_config = AGENTS.get(agent1_type, MAIN_AGENT)
    agent2_config = AGENTS.get(agent2_type, FISH_AGENT)

    # Run simulation
    result = run_simulation(
        num_hands=num_hands,
        agent1_config=agent1_config,
        agent2_config=agent2_config,
        starting_stack=starting_stack,
        small_blind=small_blind,
        big_blind=big_blind,
        verbose=False,
        show_progress=False
    )

    # Format hand results
    hands = []
    for hr in result.hand_results:
        hands.append({
            'handNumber': hr.hand_number,
            'winner': hr.winner_name,
            'amountWon': hr.amount_won,
            'description': hr.win_description,
            'agent1Cards': hr.player1_cards,
            'agent2Cards': hr.player2_cards,
            'board': hr.board,
            'agent1StackBefore': hr.player1_stack_before,
            'agent1StackAfter': hr.player1_stack_after,
            'agent2StackBefore': hr.player2_stack_before,
            'agent2StackAfter': hr.player2_stack_after,
            'actionHistory': hr.action_history,
        })

    return jsonify({
        'agent1Name': result.agent1_stats.agent_name,
        'agent2Name': result.agent2_stats.agent_name,
        'hands': hands,
        'summary': {
            'agent1Wins': result.agent1_stats.hands_won,
            'agent2Wins': result.agent2_stats.hands_won,
            'agent1Profit': result.agent1_stats.total_profit,
            'agent2Profit': result.agent2_stats.total_profit,
        }
    })


@app.route('/api/simulate/analytics', methods=['POST'])
def simulate_analytics():
    """
    Run a simulation and return comprehensive analytics for the dashboard.

    Returns per-agent: win rate, BB/100, bankroll over time, profit/loss,
    variance, action distributions by street, VPIP, PFR, aggression factor.
    """
    data = request.get_json()

    agent1_type = data.get('agent1_type', 'TAG')
    agent2_type = data.get('agent2_type', 'FISH')
    num_hands = min(int(data.get('num_hands', 200)), 10000)
    small_blind = float(data.get('small_blind', 5))
    big_blind = float(data.get('big_blind', 10))
    starting_stack = big_blind * 100  # Always 100bb buy-in

    agent1_config = AGENTS.get(agent1_type, MAIN_AGENT)
    agent2_config = AGENTS.get(agent2_type, FISH_AGENT)

    result = run_simulation(
        num_hands=num_hands,
        agent1_config=agent1_config,
        agent2_config=agent2_config,
        starting_stack=starting_stack,
        small_blind=small_blind,
        big_blind=big_blind,
        verbose=False,
        show_progress=False
    )

    def compute_agent_analytics(agent_stats, agent_name, hand_results, is_agent1):
        """Compute full analytics for one agent."""
        # Bankroll over time
        bankroll = [starting_stack]
        profits = []
        for hr in hand_results:
            if is_agent1:
                delta = hr.player1_stack_after - hr.player1_stack_before
            else:
                delta = hr.player2_stack_after - hr.player2_stack_before
            profits.append(delta)
            bankroll.append(bankroll[-1] + delta)

        # BB/100
        total_profit_bb = agent_stats.total_profit / big_blind
        bb_per_100 = (total_profit_bb / max(agent_stats.total_hands_dealt, 1)) * 100

        # Variance and std dev (in BB)
        profits_bb = [p / big_blind for p in profits]
        mean_bb = sum(profits_bb) / max(len(profits_bb), 1)
        variance_bb = sum((p - mean_bb) ** 2 for p in profits_bb) / max(len(profits_bb), 1)
        std_dev_bb = math.sqrt(variance_bb)

        # 95% confidence interval for BB/100
        n = max(len(profits_bb), 1)
        ci_margin = 1.96 * (std_dev_bb / math.sqrt(n)) * 100  # scale to per-100

        # Parse action distributions from hand histories
        actions_by_street = {
            'preflop': {'fold': 0, 'call': 0, 'raise': 0, 'check': 0},
            'flop': {'fold': 0, 'call': 0, 'raise': 0, 'check': 0},
            'turn': {'fold': 0, 'call': 0, 'raise': 0, 'check': 0},
            'river': {'fold': 0, 'call': 0, 'raise': 0, 'check': 0},
        }
        raise_sizes = []
        pfr_count = 0  # preflop raise count

        for hr in hand_results:
            current_street = 'preflop'
            for action_str in hr.action_history:
                # Detect street changes
                if action_str.startswith('FLOP:'):
                    current_street = 'flop'
                    continue
                elif action_str.startswith('TURN:'):
                    current_street = 'turn'
                    continue
                elif action_str.startswith('RIVER:'):
                    current_street = 'river'
                    continue

                # Only count actions by this agent
                if not action_str.startswith(agent_name):
                    continue
                # Skip blind postings
                if 'posts SB' in action_str or 'posts BB' in action_str:
                    continue

                action_lower = action_str.lower()
                if 'folds' in action_lower:
                    actions_by_street[current_street]['fold'] += 1
                elif 'calls' in action_lower:
                    actions_by_street[current_street]['call'] += 1
                elif 'raises' in action_lower:
                    actions_by_street[current_street]['raise'] += 1
                    if current_street == 'preflop':
                        pfr_count += 1
                    # Extract raise size
                    match = re.search(r'\$(\d+\.?\d*)', action_str)
                    if match:
                        raise_sizes.append(float(match.group(1)))
                elif 'checks' in action_lower:
                    actions_by_street[current_street]['check'] += 1
                elif 'wins' in action_lower:
                    continue

        # Compute percentages per street
        action_pcts = {}
        for street, counts in actions_by_street.items():
            total = sum(counts.values())
            if total > 0:
                action_pcts[street] = {k: round(v / total * 100, 1) for k, v in counts.items()}
            else:
                action_pcts[street] = {k: 0 for k in counts}

        # Aggression factor: (bets + raises) / calls
        total_raises = sum(s['raise'] for s in actions_by_street.values())
        total_calls = sum(s['call'] for s in actions_by_street.values())
        aggression_factor = round(total_raises / max(total_calls, 1), 2)

        # VPIP and PFR
        vpip = round(agent_stats.vpip, 1)
        pfr = round((pfr_count / max(agent_stats.total_hands_dealt, 1)) * 100, 1)

        # Raise sizing distribution (buckets in BB)
        raise_buckets = {'2-3bb': 0, '3-5bb': 0, '5-10bb': 0, '10-20bb': 0, '20+bb': 0}
        for size in raise_sizes:
            size_bb = size / big_blind
            if size_bb < 3:
                raise_buckets['2-3bb'] += 1
            elif size_bb < 5:
                raise_buckets['3-5bb'] += 1
            elif size_bb < 10:
                raise_buckets['5-10bb'] += 1
            elif size_bb < 20:
                raise_buckets['10-20bb'] += 1
            else:
                raise_buckets['20+bb'] += 1

        return {
            'name': agent_name,
            'winRate': round(agent_stats.win_rate, 1),
            'handsWon': agent_stats.hands_won,
            'handsLost': agent_stats.hands_lost,
            'totalProfitBB': round(total_profit_bb, 2),
            'bbPer100': round(bb_per_100, 2),
            'variance': round(variance_bb, 2),
            'stdDev': round(std_dev_bb, 2),
            'ciLow': round(bb_per_100 - ci_margin, 2),
            'ciHigh': round(bb_per_100 + ci_margin, 2),
            'showdownWinRate': round(agent_stats.showdown_win_rate, 1),
            'vpip': vpip,
            'pfr': pfr,
            'aggressionFactor': aggression_factor,
            'bankrollHistory': [round(b, 2) for b in bankroll],
            'actionDistribution': action_pcts,
            'raiseSizing': raise_buckets,
        }

    agent1_analytics = compute_agent_analytics(
        result.agent1_stats, agent1_config.name, result.hand_results, True
    )
    agent2_analytics = compute_agent_analytics(
        result.agent2_stats, agent2_config.name, result.hand_results, False
    )

    # Build hand history summaries for replay
    hands = []
    for hr in result.hand_results:
        hands.append({
            'handNumber': hr.hand_number,
            'winner': hr.winner_name,
            'amountWon': round(hr.amount_won, 2),
            'description': hr.win_description,
            'agent1Cards': hr.player1_cards,
            'agent2Cards': hr.player2_cards,
            'board': hr.board,
            'agent1StackBefore': round(hr.player1_stack_before, 2),
            'agent1StackAfter': round(hr.player1_stack_after, 2),
            'agent2StackBefore': round(hr.player2_stack_before, 2),
            'agent2StackAfter': round(hr.player2_stack_after, 2),
            'actionHistory': hr.action_history,
        })

    return jsonify({
        'numHands': result.num_hands,
        'bigBlind': big_blind,
        'agent1': agent1_analytics,
        'agent2': agent2_analytics,
        'hands': hands,
    })


# ========== RL Training Endpoints ==========

@app.route('/api/training/start', methods=['POST'])
def start_training():
    """
    Launch RL training as a background process.

    Request body:
    {
        "algo": "dqn" | "ppo",
        "episodes": 50000,
        "opponent": "fish" | "tag",
        "reward_mode": "shaped" | "simple" | "normalized",
        "lr": 0.0001,
        "seed": 42,
        "curriculum": false,
        "self_play": false
    }
    """
    global _training_process

    with _training_lock:
        if _training_process and _training_process.poll() is None:
            return jsonify({'error': 'Training already running'}), 409

    data = request.get_json() or {}
    algo = data.get('algo', 'dqn')
    episodes = min(int(data.get('episodes', 50000)), 200000)
    timesteps = min(int(data.get('timesteps', 200000)), 1000000)
    opponent = data.get('opponent', 'fish')
    reward_mode = data.get('reward_mode', 'shaped')
    lr = float(data.get('lr', 1e-4))
    seed = int(data.get('seed', 42))
    curriculum = data.get('curriculum', False)
    self_play = data.get('self_play', False)

    # Build command
    cmd = [
        sys.executable, os.path.join(os.path.dirname(__file__), 'train_rl.py'),
        '--algo', algo,
        '--episodes', str(episodes),
        '--timesteps', str(timesteps),
        '--opponent', opponent,
        '--reward-mode', reward_mode,
        '--lr', str(lr),
        '--seed', str(seed),
        '--log-interval', '10',
    ]

    if curriculum:
        cmd.append('--curriculum')
    if self_play:
        cmd.append('--self-play')

    # Set metrics path
    metrics_dir = os.path.join(os.path.dirname(__file__), 'metrics')
    os.makedirs(metrics_dir, exist_ok=True)
    metrics_path = os.path.join(metrics_dir, f'{algo}_metrics.json')
    cmd.extend(['--metrics-path', metrics_path])

    checkpoint_dir = os.path.join(os.path.dirname(__file__), 'models', algo)
    os.makedirs(checkpoint_dir, exist_ok=True)
    cmd.extend(['--checkpoint-dir', checkpoint_dir])

    # Clear previous metrics
    if os.path.exists(metrics_path):
        os.remove(metrics_path)

    with _training_lock:
        _training_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(__file__),
        )

    return jsonify({
        'status': 'started',
        'algo': algo,
        'episodes': episodes,
        'opponent': opponent,
        'pid': _training_process.pid,
        'metrics_path': metrics_path,
    })


@app.route('/api/training/stop', methods=['POST'])
def stop_training():
    """Stop running training process."""
    global _training_process

    with _training_lock:
        if _training_process and _training_process.poll() is None:
            _training_process.terminate()
            try:
                _training_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _training_process.kill()
            _training_process = None
            return jsonify({'status': 'stopped'})

    return jsonify({'status': 'no_training_running'})


@app.route('/api/training/status', methods=['GET'])
def training_status():
    """Get current training status and metrics."""
    global _training_process

    running = False
    with _training_lock:
        if _training_process and _training_process.poll() is None:
            running = True

    # Load metrics from file
    metrics_dir = os.path.join(os.path.dirname(__file__), 'metrics')
    metrics = None
    metrics_path = None

    # Try to find the latest metrics file
    for algo in ['dqn', 'ppo']:
        path = os.path.join(metrics_dir, f'{algo}_metrics.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    metrics = json.load(f)
                    metrics_path = path
                break
            except (json.JSONDecodeError, IOError):
                pass

    return jsonify({
        'running': running,
        'metrics': metrics,
        'metrics_path': metrics_path,
    })


@app.route('/api/training/metrics', methods=['GET'])
def training_metrics():
    """
    Get training metrics. Supports polling and optional tail parameter.

    Query params:
        algo: "dqn" | "ppo" (default: "dqn")
        tail: number of most recent metric points to return (default: all)
    """
    algo = request.args.get('algo', 'dqn')
    tail = request.args.get('tail', None)

    metrics_path = os.path.join(os.path.dirname(__file__), 'metrics', f'{algo}_metrics.json')

    if not os.path.exists(metrics_path):
        return jsonify({'error': 'No metrics found', 'metrics': None}), 404

    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return jsonify({'error': 'Metrics file corrupted', 'metrics': None}), 500

    if tail:
        tail = int(tail)
        if 'metrics' in data and data['metrics']:
            data['metrics'] = data['metrics'][-tail:]

    return jsonify(data)


@app.route('/api/training/metrics/stream', methods=['GET'])
def training_metrics_stream():
    """
    Server-Sent Events (SSE) stream for live training metrics.

    The frontend connects to this endpoint and receives metrics updates in real-time.

    Query params:
        algo: "dqn" | "ppo" (default: "dqn")
    """
    algo = request.args.get('algo', 'dqn')
    metrics_path = os.path.join(os.path.dirname(__file__), 'metrics', f'{algo}_metrics.json')

    def generate():
        last_count = 0
        while True:
            try:
                if os.path.exists(metrics_path):
                    with open(metrics_path, 'r') as f:
                        data = json.load(f)

                    metrics_list = data.get('metrics', [])
                    current_count = len(metrics_list)

                    if current_count > last_count:
                        # Send new metrics since last check
                        new_metrics = metrics_list[last_count:]
                        for m in new_metrics:
                            yield f"data: {json.dumps(m)}\n\n"
                        last_count = current_count

                    # Check if training is still running
                    global _training_process
                    is_running = _training_process and _training_process.poll() is None
                    if not is_running and current_count > 0 and current_count == last_count:
                        yield f"data: {json.dumps({'type': 'complete', 'total_metrics': current_count})}\n\n"
                        break

            except (json.JSONDecodeError, IOError, FileNotFoundError):
                pass

            time.sleep(1)  # Poll interval

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/training/evaluate', methods=['POST'])
def evaluate_rl_agent():
    """
    Evaluate a trained RL agent against an opponent.

    Request body:
    {
        "checkpoint": "dqn_best",
        "opponent": "fish" | "tag" | "random",
        "games": 1000
    }
    """
    data = request.get_json() or {}
    checkpoint_name = data.get('checkpoint', 'dqn_best')
    opponent = data.get('opponent', 'fish')
    num_games = min(int(data.get('games', 500)), 5000)

    checkpoint_path = os.path.join(
        os.path.dirname(__file__), 'models', 'dqn', f'{checkpoint_name}.pt'
    )

    if not os.path.exists(checkpoint_path):
        return jsonify({'error': f'Checkpoint not found: {checkpoint_name}.pt'}), 404

    try:
        # Import here to avoid loading torch at startup if not needed
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
        from rl_brain import RLBrain

        rl_brain = RLBrain(checkpoint_path=checkpoint_path, device="cpu", epsilon=0.0)
        rl_config = AgentConfig(name='RL Agent', brain_module=rl_brain, description='Trained DQN')

        if opponent == 'tag':
            opp_config = AGENTS['TAG']
        elif opponent == 'random':
            random_brain = RLBrain(checkpoint_path=None, device="cpu", epsilon=1.0)
            opp_config = AgentConfig(name='Random', brain_module=random_brain, description='Random')
        else:
            opp_config = AGENTS['FISH']

        big_blind = 10.0
        starting_stack = big_blind * 100

        result = run_simulation(
            num_hands=num_games,
            agent1_config=rl_config,
            agent2_config=opp_config,
            starting_stack=starting_stack,
            small_blind=5.0,
            big_blind=big_blind,
            verbose=False,
            show_progress=False,
        )

        s1 = result.agent1_stats
        profits_bb = []
        for hr in result.hand_results:
            delta = hr.player1_stack_after - hr.player1_stack_before
            profits_bb.append(delta / big_blind)

        mean_profit = sum(profits_bb) / max(len(profits_bb), 1)
        std_profit = (sum((p - mean_profit)**2 for p in profits_bb) / max(len(profits_bb), 1)) ** 0.5
        bb_per_100 = mean_profit * 100
        n = len(profits_bb)
        ci_margin = 1.96 * (std_profit / max(n, 1)**0.5) * 100

        return jsonify({
            'opponent': opponent,
            'games': num_games,
            'win_rate': round(s1.win_rate, 2),
            'hands_won': s1.hands_won,
            'hands_lost': s1.hands_lost,
            'total_profit_bb': round(s1.total_profit / big_blind, 2),
            'bb_per_100': round(bb_per_100, 2),
            'ci_low': round(bb_per_100 - ci_margin, 2),
            'ci_high': round(bb_per_100 + ci_margin, 2),
            'vpip': round(s1.vpip, 1),
            'showdown_win_rate': round(s1.showdown_win_rate, 1),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/training/checkpoints', methods=['GET'])
def list_checkpoints():
    """List available model checkpoints."""
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    checkpoints = []

    if os.path.exists(models_dir):
        for algo_dir in ['dqn', 'ppo']:
            algo_path = os.path.join(models_dir, algo_dir)
            if os.path.exists(algo_path):
                for f in os.listdir(algo_path):
                    if f.endswith('.pt') or f.endswith('.zip'):
                        stat = os.stat(os.path.join(algo_path, f))
                        checkpoints.append({
                            'name': f.rsplit('.', 1)[0],
                            'algo': algo_dir,
                            'filename': f,
                            'size_mb': round(stat.st_size / (1024*1024), 2),
                            'modified': stat.st_mtime,
                        })

    checkpoints.sort(key=lambda c: c['modified'], reverse=True)
    return jsonify({'checkpoints': checkpoints})


@app.route('/api/training/reload-rl', methods=['POST'])
def reload_rl_agent():
    """Reload the RL agent from the latest checkpoint into the AGENTS registry."""
    global _rl_brain_cache

    data = request.get_json() or {}
    checkpoint_name = data.get('checkpoint', 'dqn_best')

    # Clear cache
    _rl_brain_cache.pop(checkpoint_name, None)

    brain = _get_rl_brain(checkpoint_name)
    if brain:
        AGENTS['RL'] = AgentConfig(name='RL Agent', brain_module=brain, description='Trained DQN Agent')
        return jsonify({'status': 'loaded', 'checkpoint': checkpoint_name})
    else:
        return jsonify({'error': f'Checkpoint {checkpoint_name} not found'}), 404


if __name__ == '__main__':
    print("Starting Poker Engine API on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)