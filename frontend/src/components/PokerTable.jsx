import React, { useState, useCallback, useRef } from 'react';
import { Card, CardGrid, EmptyCardSlot } from './Card';

// Game phases
const PHASES = {
  WAITING: 'waiting',
  PREFLOP: 'preflop',
  FLOP: 'flop',
  TURN: 'turn',
  RIVER: 'river',
  SHOWDOWN: 'showdown',
};

// Initial game state
const createInitialState = () => ({
  phase: PHASES.WAITING,
  pot: 0,
  playerStack: 200,
  opponentStack: 200,
  playerCards: [],
  opponentCards: [],
  communityCards: [],
  playerBet: 0,
  opponentBet: 0,
  isPlayerTurn: true,
  lastAction: null,
  agentThinking: null,
  winner: null,
  handNumber: 0,
  smallBlind: 1,
  bigBlind: 2,
});

// Simple deck for demo (full integration with backend in Step 14)
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

/**
 * PokerTable component - Main game interface
 */
function PokerTable() {
  const [gameState, setGameState] = useState(createInitialState());
  const deckRef = useRef([]);

  // Advance to next phase and deal community cards
  const advancePhase = useCallback((state) => {
    let newPhase = state.phase;
    let newCommunityCards = [...state.communityCards];

    switch (state.phase) {
      case PHASES.PREFLOP:
        newPhase = PHASES.FLOP;
        // Deal 3 cards for flop
        newCommunityCards = [deckRef.current.pop(), deckRef.current.pop(), deckRef.current.pop()];
        break;
      case PHASES.FLOP:
        newPhase = PHASES.TURN;
        newCommunityCards.push(deckRef.current.pop());
        break;
      case PHASES.TURN:
        newPhase = PHASES.RIVER;
        newCommunityCards.push(deckRef.current.pop());
        break;
      case PHASES.RIVER:
        newPhase = PHASES.SHOWDOWN;
        // Determine winner (simplified - random for demo)
        const winner = Math.random() > 0.5 ? 'player' : 'opponent';
        return {
          ...state,
          phase: newPhase,
          communityCards: newCommunityCards,
          playerBet: 0,
          opponentBet: 0,
          winner,
          playerStack: winner === 'player' ? state.playerStack + state.pot : state.playerStack,
          opponentStack: winner === 'opponent' ? state.opponentStack + state.pot : state.opponentStack,
        };
      default:
        break;
    }

    return {
      ...state,
      phase: newPhase,
      communityCards: newCommunityCards,
      playerBet: 0,
      opponentBet: 0,
      isPlayerTurn: false,
    };
  }, []);

  // Simulate agent decision (placeholder - will connect to backend in Step 14)
  const simulateAgentAction = useCallback(() => {
    setGameState((prev) => {
      if (prev.phase === PHASES.SHOWDOWN || prev.phase === PHASES.WAITING) {
        return prev;
      }

      // Simple agent logic: 70% check/call, 20% raise, 10% fold
      const rand = Math.random();
      let newState;

      if (rand < 0.1 && prev.pot > prev.bigBlind * 4) {
        // Fold (rarely, and only if pot is large)
        newState = {
          ...prev,
          winner: 'player',
          phase: PHASES.SHOWDOWN,
          lastAction: { player: 'Agent', action: 'Fold' },
          agentThinking: 'Hand too weak to continue.',
          playerStack: prev.playerStack + prev.pot,
        };
      } else if (rand < 0.3) {
        // Raise
        const raiseAmount = prev.bigBlind * 2;
        const totalBet = prev.playerBet + raiseAmount;
        newState = {
          ...prev,
          pot: prev.pot + (totalBet - prev.opponentBet),
          opponentStack: prev.opponentStack - (totalBet - prev.opponentBet),
          opponentBet: totalBet,
          isPlayerTurn: true,
          lastAction: { player: 'Agent', action: `Raise to $${totalBet}` },
          agentThinking: 'Strong hand, building the pot.',
        };
      } else {
        // Check/Call
        const callAmount = prev.playerBet - prev.opponentBet;
        const action = callAmount > 0 ? `Call $${callAmount}` : 'Check';

        // Advance phase since both players have acted
        newState = advancePhase({
          ...prev,
          pot: prev.pot + Math.max(0, callAmount),
          opponentStack: prev.opponentStack - Math.max(0, callAmount),
          opponentBet: prev.playerBet,
          lastAction: { player: 'Agent', action },
          agentThinking: callAmount > 0 ? 'Pot odds are good, calling.' : 'Checking to see more cards.',
        });
        newState.isPlayerTurn = true;
      }

      return newState;
    });
  }, [advancePhase]);

  // Deal a new hand
  const dealNewHand = useCallback(() => {
    const newDeck = createDeck();
    const playerCards = [newDeck.pop(), newDeck.pop()];
    const opponentCards = [newDeck.pop(), newDeck.pop()];

    deckRef.current = newDeck;
    setGameState((prev) => {
      const newPlayerStack = prev.playerStack - prev.smallBlind;
      const newOpponentStack = prev.opponentStack - prev.bigBlind;
      return {
        ...createInitialState(),
        playerStack: newPlayerStack,
        opponentStack: newOpponentStack,
        handNumber: prev.handNumber + 1,
        phase: PHASES.PREFLOP,
        playerCards,
        opponentCards,
        playerBet: prev.smallBlind,
        opponentBet: prev.bigBlind,
        pot: prev.smallBlind + prev.bigBlind,
        isPlayerTurn: true,
      };
    });
  }, []);

  // Player actions
  const handleFold = useCallback(() => {
    setGameState((prev) => ({
      ...prev,
      winner: 'opponent',
      phase: PHASES.SHOWDOWN,
      lastAction: { player: 'You', action: 'Fold' },
      opponentStack: prev.opponentStack + prev.pot,
    }));
  }, []);

  const handleCall = useCallback(() => {
    setGameState((prev) => {
      const callAmount = prev.opponentBet - prev.playerBet;
      const newPot = prev.pot + callAmount;
      const newPlayerStack = prev.playerStack - callAmount;

      // Advance to next phase after call
      const advancedState = advancePhase({
        ...prev,
        pot: newPot,
        playerStack: newPlayerStack,
        playerBet: prev.opponentBet,
        lastAction: { player: 'You', action: callAmount > 0 ? `Call $${callAmount}` : 'Check' },
      });

      // Schedule agent action if not at showdown
      if (advancedState.phase !== PHASES.SHOWDOWN) {
        setTimeout(() => simulateAgentAction(), 1000);
      }

      return advancedState;
    });
  }, [advancePhase, simulateAgentAction]);

  const handleRaise = useCallback((amount) => {
    setGameState((prev) => {
      const totalBet = prev.opponentBet + amount;
      const raiseAmount = totalBet - prev.playerBet;
      const newPlayerStack = prev.playerStack - raiseAmount;

      // Simulate agent response after a delay
      setTimeout(() => simulateAgentAction(), 1000);

      return {
        ...prev,
        pot: prev.pot + raiseAmount,
        playerStack: newPlayerStack,
        playerBet: totalBet,
        isPlayerTurn: false,
        lastAction: { player: 'You', action: `Raise to $${totalBet}` },
      };
    });
  }, [simulateAgentAction]);

  const { phase, pot, playerStack, opponentStack, playerCards, opponentCards,
          communityCards, playerBet, opponentBet, isPlayerTurn, lastAction,
          agentThinking, winner, handNumber } = gameState;

  const callAmount = opponentBet - playerBet;
  const canCheck = callAmount === 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-felt-green to-felt-green-light p-4">
      <div className="max-w-4xl mx-auto">
        {/* Game Info Header */}
        <div className="flex justify-between items-center mb-4 text-white">
          <div className="text-lg">Hand #{handNumber || '-'}</div>
          <div className="text-lg font-semibold">
            Phase: {phase.charAt(0).toUpperCase() + phase.slice(1)}
          </div>
          <div className="text-lg">Blinds: $1/$2</div>
        </div>

        {/* Poker Table */}
        <div className="bg-gradient-to-b from-green-800 to-green-900 rounded-3xl p-8 shadow-2xl border-8 border-amber-900">
          {/* Opponent Area */}
          <div className="flex flex-col items-center mb-8">
            <div className="text-white mb-2 flex items-center gap-4">
              <span className="text-lg font-semibold">Agent (TAG)</span>
              <span className="bg-gray-800 px-3 py-1 rounded-full text-sm">
                Stack: ${opponentStack}
              </span>
              {opponentBet > 0 && (
                <span className="bg-yellow-600 px-3 py-1 rounded-full text-sm">
                  Bet: ${opponentBet}
                </span>
              )}
            </div>
            <div className="flex gap-2">
              {phase === PHASES.WAITING ? (
                <>
                  <EmptyCardSlot size="md" />
                  <EmptyCardSlot size="md" />
                </>
              ) : phase === PHASES.SHOWDOWN && winner ? (
                <CardGrid cards={opponentCards} size="md" />
              ) : (
                <>
                  <Card faceDown size="md" />
                  <Card faceDown size="md" />
                </>
              )}
            </div>
          </div>

          {/* Community Cards & Pot */}
          <div className="flex flex-col items-center my-8">
            {/* Pot */}
            <div className="bg-gray-900/60 rounded-full px-6 py-2 mb-4">
              <span className="text-yellow-400 font-bold text-xl">Pot: ${pot}</span>
            </div>

            {/* Community Cards */}
            <div className="flex gap-2 min-h-24 items-center">
              {phase === PHASES.WAITING || phase === PHASES.PREFLOP ? (
                <div className="flex gap-2">
                  {[...Array(5)].map((_, i) => (
                    <EmptyCardSlot key={i} size="md" />
                  ))}
                </div>
              ) : (
                <>
                  <CardGrid cards={communityCards} size="md" animate />
                  {/* Empty slots for remaining cards */}
                  {[...Array(5 - communityCards.length)].map((_, i) => (
                    <EmptyCardSlot key={`empty-${i}`} size="md" />
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Player Area */}
          <div className="flex flex-col items-center mt-8">
            <div className="flex gap-2 mb-2">
              {phase === PHASES.WAITING ? (
                <>
                  <EmptyCardSlot size="lg" />
                  <EmptyCardSlot size="lg" />
                </>
              ) : (
                <CardGrid cards={playerCards} size="lg" />
              )}
            </div>
            <div className="text-white mt-2 flex items-center gap-4">
              <span className="text-lg font-semibold">You</span>
              <span className="bg-gray-800 px-3 py-1 rounded-full text-sm">
                Stack: ${playerStack}
              </span>
              {playerBet > 0 && (
                <span className="bg-yellow-600 px-3 py-1 rounded-full text-sm">
                  Bet: ${playerBet}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Panel */}
        <div className="mt-6 bg-gray-800 rounded-xl p-6 shadow-xl">
          {/* Last Action & Agent Thinking */}
          {(lastAction || agentThinking) && (
            <div className="mb-4 p-3 bg-gray-700/50 rounded-lg">
              {lastAction && (
                <p className="text-gray-300">
                  <span className="font-semibold">{lastAction.player}:</span> {lastAction.action}
                </p>
              )}
              {agentThinking && (
                <p className="text-blue-400 text-sm mt-1 italic">
                  Agent thinking: "{agentThinking}"
                </p>
              )}
            </div>
          )}

          {/* Winner Message */}
          {winner && (
            <div className={`mb-4 p-4 rounded-lg text-center text-xl font-bold ${
              winner === 'player' ? 'bg-green-600/50 text-green-200' : 'bg-red-600/50 text-red-200'
            }`}>
              {winner === 'player' ? 'You Win!' : 'Agent Wins!'}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-center gap-4">
            {phase === PHASES.WAITING || phase === PHASES.SHOWDOWN ? (
              <button
                onClick={dealNewHand}
                className="px-8 py-3 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-bold rounded-lg text-lg transition-colors"
              >
                {phase === PHASES.SHOWDOWN ? 'Next Hand' : 'Deal Cards'}
              </button>
            ) : isPlayerTurn ? (
              <>
                <button
                  onClick={handleFold}
                  className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg transition-colors"
                >
                  Fold
                </button>
                <button
                  onClick={handleCall}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-colors"
                >
                  {canCheck ? 'Check' : `Call $${callAmount}`}
                </button>
                <button
                  onClick={() => handleRaise(gameState.bigBlind * 2)}
                  className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-bold rounded-lg transition-colors"
                >
                  Raise ${gameState.bigBlind * 2}
                </button>
                <button
                  onClick={() => handleRaise(playerStack)}
                  disabled={playerStack <= 0}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 text-white font-bold rounded-lg transition-colors"
                >
                  All In
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2 text-gray-400">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-gray-400 border-t-transparent"></div>
                <span>Agent is thinking...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PokerTable;
