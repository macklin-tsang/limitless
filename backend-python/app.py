"""
Flask API wrapper for the Poker Engine.
Provides endpoints for running simulations and single hands.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

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

# Agent configurations
AGENTS = {
    'TAG': AgentConfig(name='TAG Agent', brain_module=main_brain, description='Tight-Aggressive'),
    'FISH': AgentConfig(name='Fish', brain_module=fish_brain, description='Calling Station'),
    'MAIN': MAIN_AGENT,
}


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

    # Run simulation
    result = run_simulation(
        num_hands=num_games,
        agent1_config=agent1,
        agent2_config=agent2,
        starting_stack=1000.0,
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
    starting_stack = float(data.get('starting_stack', 1000))

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
    starting_stack = float(data.get('starting_stack', 1000))

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


if __name__ == '__main__':
    print("Starting Poker Engine API on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)