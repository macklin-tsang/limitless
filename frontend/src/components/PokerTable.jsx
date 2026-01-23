import { useState, useCallback } from 'react';
import { CardGrid, EmptyCardSlot } from './Card';

// Game phases
const PHASES = {
  WAITING: 'waiting',
  PREFLOP: 'preflop',
  FLOP: 'flop',
  TURN: 'turn',
  RIVER: 'river',
  SHOWDOWN: 'showdown',
};

// API base URL for Python backend
const PYTHON_API_URL = process.env.REACT_APP_PYTHON_API_URL || 'http://localhost:5000/api';

/**
 * PokerTable component - Agent vs Agent simulation interface
 */
function PokerTable() {
  const [gameState, setGameState] = useState({
    phase: PHASES.WAITING,
    pot: 0,
    agent1Stack: 1000,
    agent2Stack: 1000,
    agent1Cards: [],
    agent2Cards: [],
    communityCards: [],
    winner: null,
    handNumber: 0,
    smallBlind: 5,
    bigBlind: 10,
    actionHistory: [],
    isLoading: false,
    error: null,
  });

  // Run a single hand simulation
  const runSimulation = useCallback(async () => {
    setGameState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${PYTHON_API_URL}/simulate/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent1_type: 'TAG',
          agent2_type: 'FISH',
          small_blind: 5,
          big_blind: 10,
          starting_stack: gameState.agent1Stack,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to run simulation');
      }

      const data = await response.json();

      // Parse cards from response
      const agent1Cards = data.agent1?.cards || [];
      const agent2Cards = data.agent2?.cards || [];
      const boardCards = data.board || [];

      // Determine phase based on board length
      let phase = PHASES.SHOWDOWN;
      if (boardCards.length === 0 && !data.wentToShowdown) {
        phase = PHASES.PREFLOP;
      }

      setGameState(prev => ({
        ...prev,
        phase,
        pot: data.pot || 0,
        agent1Stack: data.agent1?.stackAfter || prev.agent1Stack,
        agent2Stack: data.agent2?.stackAfter || prev.agent2Stack,
        agent1Cards,
        agent2Cards,
        communityCards: boardCards,
        winner: data.winner,
        handNumber: prev.handNumber + 1,
        actionHistory: data.actionHistory || [],
        isLoading: false,
      }));
    } catch (err) {
      // Fallback to local simulation if backend unavailable
      console.warn('Python backend unavailable, using local simulation:', err.message);
      runLocalSimulation();
    }
  }, [gameState.agent1Stack]);

  // Local fallback simulation (simplified)
  const runLocalSimulation = useCallback(() => {
    const createDeck = () => {
      const ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'];
      const suits = ['h', 'd', 'c', 's'];
      const deck = [];
      for (const suit of suits) {
        for (const rank of ranks) {
          deck.push({ rank, suit });
        }
      }
      // Shuffle
      for (let i = deck.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [deck[i], deck[j]] = [deck[j], deck[i]];
      }
      return deck;
    };

    const deck = createDeck();
    const agent1Cards = [deck.pop(), deck.pop()];
    const agent2Cards = [deck.pop(), deck.pop()];

    // Burn and deal community cards
    deck.pop(); // burn
    const flop = [deck.pop(), deck.pop(), deck.pop()];
    deck.pop(); // burn
    const turn = deck.pop();
    deck.pop(); // burn
    const river = deck.pop();

    const communityCards = [...flop, turn, river];
    const pot = 30; // Simplified pot
    const winner = Math.random() > 0.5 ? 'TAG Agent' : 'Fish';

    const actionHistory = [
      'TAG Agent posts SB $5.00',
      'Fish posts BB $10.00',
      'TAG Agent raises to $30.00',
      'Fish calls $20.00',
      `FLOP: ${flop.map(c => c.rank + c.suit).join(', ')}`,
      'Fish checks',
      'TAG Agent bets $15.00',
      'Fish calls $15.00',
      `TURN: ${turn.rank}${turn.suit}`,
      'Fish checks',
      'TAG Agent checks',
      `RIVER: ${river.rank}${river.suit}`,
      'Fish checks',
      'TAG Agent checks',
      `${winner} wins $${pot}.00`,
    ];

    setGameState(prev => {
      const winAmount = pot;
      const agent1Wins = winner === 'TAG Agent';
      return {
        ...prev,
        phase: PHASES.SHOWDOWN,
        pot,
        agent1Stack: agent1Wins ? prev.agent1Stack + winAmount - 30 : prev.agent1Stack - 30,
        agent2Stack: agent1Wins ? prev.agent2Stack - 30 : prev.agent2Stack + winAmount - 30,
        agent1Cards,
        agent2Cards,
        communityCards,
        winner,
        handNumber: prev.handNumber + 1,
        actionHistory,
        isLoading: false,
      };
    });
  }, []);

  // Reset stacks to starting amount
  const handleTopUp = useCallback(() => {
    setGameState(prev => ({
      ...prev,
      agent1Stack: 1000,
      agent2Stack: 1000,
      phase: PHASES.WAITING,
      agent1Cards: [],
      agent2Cards: [],
      communityCards: [],
      winner: null,
      actionHistory: [],
      pot: 0,
    }));
  }, []);

  const { phase, pot, agent1Stack, agent2Stack, agent1Cards, agent2Cards,
          communityCards, winner, handNumber, actionHistory, isLoading } = gameState;

  // Check if either stack is too low to continue
  const needsTopUp = agent1Stack < 15 || agent2Stack < 15;

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Game Info Header */}
        <div className="flex justify-between items-center mb-4 text-gray-800">
          <div className="text-lg font-medium">Hand #{handNumber || '-'}</div>
          <div className="text-lg font-semibold">
            {phase === PHASES.WAITING ? 'Ready' : phase.charAt(0).toUpperCase() + phase.slice(1)}
          </div>
          <div className="text-lg">Blinds: $5/$10</div>
        </div>

        <div className="flex gap-6">
          {/* Main Table Area */}
          <div className="flex-1">
            {/* Poker Table */}
            <div className="bg-gradient-to-b from-green-700 to-green-800 rounded-3xl p-8 shadow-2xl border-8 border-amber-800">
              {/* Agent 1 Area (Top) */}
              <div className="flex flex-col items-center mb-6">
                <div className="text-white mb-2 flex items-center gap-4">
                  <span className="text-lg font-semibold">TAG Agent</span>
                  <span className={`px-3 py-1 rounded-full text-sm ${agent1Stack < 100 ? 'bg-red-600' : 'bg-gray-800'}`}>
                    Stack: ${agent1Stack}
                  </span>
                </div>
                <div className="flex gap-2">
                  {phase === PHASES.WAITING ? (
                    <>
                      <EmptyCardSlot size="md" />
                      <EmptyCardSlot size="md" />
                    </>
                  ) : (
                    <CardGrid cards={agent1Cards} size="md" />
                  )}
                </div>
              </div>

              {/* Community Cards & Pot */}
              <div className="flex flex-col items-center my-6">
                {/* Pot */}
                <div className="bg-gray-900/60 rounded-full px-6 py-2 mb-4">
                  <span className="text-yellow-400 font-bold text-xl">Pot: ${pot}</span>
                </div>

                {/* Community Cards */}
                <div className="flex gap-2 min-h-28 items-center">
                  {phase === PHASES.WAITING ? (
                    <div className="flex gap-2">
                      {[...Array(5)].map((_, i) => (
                        <EmptyCardSlot key={i} size="md" />
                      ))}
                    </div>
                  ) : (
                    <>
                      <CardGrid cards={communityCards} size="md" animate />
                      {/* Empty slots for remaining cards */}
                      {[...Array(Math.max(0, 5 - communityCards.length))].map((_, i) => (
                        <EmptyCardSlot key={`empty-${i}`} size="md" />
                      ))}
                    </>
                  )}
                </div>
              </div>

              {/* Agent 2 Area (Bottom) */}
              <div className="flex flex-col items-center mt-6">
                <div className="flex gap-2 mb-2">
                  {phase === PHASES.WAITING ? (
                    <>
                      <EmptyCardSlot size="md" />
                      <EmptyCardSlot size="md" />
                    </>
                  ) : (
                    <CardGrid cards={agent2Cards} size="md" />
                  )}
                </div>
                <div className="text-white mt-2 flex items-center gap-4">
                  <span className="text-lg font-semibold">Fish</span>
                  <span className={`px-3 py-1 rounded-full text-sm ${agent2Stack < 100 ? 'bg-red-600' : 'bg-gray-800'}`}>
                    Stack: ${agent2Stack}
                  </span>
                </div>
              </div>
            </div>

            {/* Action Panel */}
            <div className="mt-6 bg-white rounded-xl p-6 shadow-lg border border-gray-200">
              {/* Winner Message */}
              {winner && (
                <div className={`mb-4 p-4 rounded-lg text-center text-xl font-bold ${
                  winner === 'TAG Agent' ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-blue-100 text-blue-800 border border-blue-300'
                }`}>
                  {winner} Wins!
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-center gap-4">
                {needsTopUp ? (
                  <button
                    onClick={handleTopUp}
                    className="px-8 py-3 bg-orange-500 hover:bg-orange-400 text-white font-bold rounded-lg text-lg transition-colors"
                  >
                    Top Up Stacks
                  </button>
                ) : (
                  <button
                    onClick={runSimulation}
                    disabled={isLoading}
                    className="px-8 py-3 bg-yellow-500 hover:bg-yellow-400 disabled:bg-gray-400 text-gray-900 font-bold rounded-lg text-lg transition-colors"
                  >
                    {isLoading ? (
                      <span className="flex items-center gap-2">
                        <span className="animate-spin rounded-full h-5 w-5 border-2 border-gray-900 border-t-transparent"></span>
                        Simulating...
                      </span>
                    ) : (
                      phase === PHASES.WAITING ? 'Run Simulation' : 'Next Hand'
                    )}
                  </button>
                )}

                {phase !== PHASES.WAITING && (
                  <button
                    onClick={handleTopUp}
                    className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold rounded-lg transition-colors"
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Action History Panel */}
          <div className="w-80 bg-white rounded-xl shadow-lg border border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800">Action History</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 max-h-[600px]">
              {actionHistory.length === 0 ? (
                <p className="text-gray-500 text-sm italic">
                  Run a simulation to see the action history
                </p>
              ) : (
                <div className="space-y-1">
                  {actionHistory.map((action, index) => {
                    // Style different action types
                    let textClass = 'text-gray-700';
                    if (action.includes('FLOP') || action.includes('TURN') || action.includes('RIVER')) {
                      textClass = 'text-blue-600 font-medium';
                    } else if (action.includes('wins')) {
                      textClass = 'text-green-600 font-bold';
                    } else if (action.includes('folds')) {
                      textClass = 'text-red-600';
                    } else if (action.includes('raises') || action.includes('bets')) {
                      textClass = 'text-orange-600';
                    } else if (action.includes('all-in')) {
                      textClass = 'text-purple-600 font-bold';
                    }

                    return (
                      <p key={index} className={`text-sm ${textClass}`}>
                        {action}
                      </p>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PokerTable;