import React from 'react';

// Suit symbols and colors
const SUITS = {
  h: { symbol: '♥', color: 'text-red-600', name: 'hearts' },
  d: { symbol: '♦', color: 'text-red-600', name: 'diamonds' },
  c: { symbol: '♣', color: 'text-gray-900', name: 'clubs' },
  s: { symbol: '♠', color: 'text-gray-900', name: 'spades' },
};

// Rank display (T = 10)
const RANKS = {
  '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
  '7': '7', '8': '8', '9': '9', 'T': '10',
  'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A',
};

/**
 * Card component for displaying a playing card
 *
 * @param {string} rank - Card rank (2-9, T, J, Q, K, A)
 * @param {string} suit - Card suit (h, d, c, s)
 * @param {boolean} faceDown - Whether the card is face down
 * @param {boolean} highlighted - Whether to show highlight animation
 * @param {string} size - Card size: 'sm', 'md', 'lg'
 * @param {boolean} animate - Whether to animate deal
 * @param {function} onClick - Click handler
 */
function Card({
  rank,
  suit,
  faceDown = false,
  highlighted = false,
  size = 'md',
  animate = false,
  onClick,
}) {
  // Size classes
  const sizeClasses = {
    sm: 'w-12 h-16 text-sm',
    md: 'w-16 h-22 text-base',
    lg: 'w-24 h-32 text-xl',
  };

  const suitData = SUITS[suit] || SUITS.s;
  const displayRank = RANKS[rank] || rank;

  // Base card styles
  const baseClasses = `
    relative rounded-lg shadow-card
    flex flex-col items-center justify-between
    p-1 cursor-pointer select-none
    transition-all duration-200
    hover:shadow-card-hover hover:-translate-y-1
    ${sizeClasses[size]}
    ${animate ? 'animate-deal' : ''}
    ${highlighted ? 'animate-highlight ring-2 ring-yellow-400' : ''}
    ${onClick ? 'cursor-pointer' : 'cursor-default'}
  `;

  // Face down card (card back)
  if (faceDown) {
    return (
      <div
        className={`${baseClasses} bg-gradient-to-br from-blue-800 to-blue-900 border-2 border-blue-700`}
        onClick={onClick}
        role="img"
        aria-label="Face-down card"
      >
        <div className="absolute inset-1 border border-blue-600 rounded-md">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-3/4 h-3/4 rounded border border-blue-500 bg-gradient-to-br from-blue-700 to-blue-800">
              {/* Diamond pattern */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="grid grid-cols-3 gap-0.5 transform rotate-45 scale-75">
                  {[...Array(9)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 bg-blue-400 rounded-sm"
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Face up card
  return (
    <div
      className={`${baseClasses} bg-white border border-gray-200`}
      onClick={onClick}
      role="img"
      aria-label={`${displayRank} of ${suitData.name}`}
    >
      {/* Top-left corner */}
      <div className={`absolute top-1 left-1 ${suitData.color} font-bold leading-tight`}>
        <div className="text-center">{displayRank}</div>
        <div className="text-center -mt-1">{suitData.symbol}</div>
      </div>

      {/* Center suit symbol */}
      <div className={`absolute inset-0 flex items-center justify-center ${suitData.color}`}>
        <span className={size === 'lg' ? 'text-4xl' : size === 'md' ? 'text-2xl' : 'text-xl'}>
          {suitData.symbol}
        </span>
      </div>

      {/* Bottom-right corner (rotated) */}
      <div className={`absolute bottom-1 right-1 ${suitData.color} font-bold leading-tight rotate-180`}>
        <div className="text-center">{displayRank}</div>
        <div className="text-center -mt-1">{suitData.symbol}</div>
      </div>
    </div>
  );
}

/**
 * CardGrid component for displaying multiple cards
 *
 * @param {Array} cards - Array of card objects with {rank, suit}
 * @param {boolean} faceDown - Whether all cards are face down
 * @param {string} size - Card size
 * @param {boolean} animate - Whether to animate cards
 * @param {number} highlightIndex - Index of card to highlight
 */
function CardGrid({
  cards = [],
  faceDown = false,
  size = 'md',
  animate = false,
  highlightIndex = -1,
}) {
  if (!cards || cards.length === 0) {
    return null;
  }

  // Filter out any undefined or invalid cards
  const validCards = cards.filter(card => card && card.rank && card.suit);

  if (validCards.length === 0) {
    return null;
  }

  return (
    <div className="flex gap-2 justify-center">
      {validCards.map((card, index) => (
        <Card
          key={`${card.rank}${card.suit}-${index}`}
          rank={card.rank}
          suit={card.suit}
          faceDown={faceDown}
          size={size}
          animate={animate}
          highlighted={index === highlightIndex}
        />
      ))}
    </div>
  );
}

/**
 * EmptyCardSlot component for showing placeholder
 */
function EmptyCardSlot({ size = 'md' }) {
  const sizeClasses = {
    sm: 'w-12 h-16',
    md: 'w-16 h-22',
    lg: 'w-24 h-32',
  };

  return (
    <div
      className={`
        ${sizeClasses[size]}
        rounded-lg border-2 border-dashed border-gray-600
        bg-gray-800/30
        flex items-center justify-center
      `}
    >
      <span className="text-gray-600 text-xs">?</span>
    </div>
  );
}

export { Card, CardGrid, EmptyCardSlot, SUITS, RANKS };
export default Card;
