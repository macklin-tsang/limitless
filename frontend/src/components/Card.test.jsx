import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Card, CardGrid, EmptyCardSlot, SUITS, RANKS } from './Card';

describe('Card Component', () => {
  describe('Face-up cards', () => {
    test('renders card with correct rank and suit symbol', () => {
      render(<Card rank="A" suit="s" />);
      // Should have Ace of spades displayed
      expect(screen.getByRole('img')).toHaveAttribute('aria-label', 'A of spades');
    });

    test('renders hearts with red color', () => {
      const { container } = render(<Card rank="K" suit="h" />);
      // Should contain heart symbol
      expect(container.textContent).toContain('♥');
    });

    test('renders diamonds with red color', () => {
      const { container } = render(<Card rank="Q" suit="d" />);
      expect(container.textContent).toContain('♦');
    });

    test('renders clubs with black color', () => {
      const { container } = render(<Card rank="J" suit="c" />);
      expect(container.textContent).toContain('♣');
    });

    test('renders spades with black color', () => {
      const { container } = render(<Card rank="T" suit="s" />);
      expect(container.textContent).toContain('♠');
    });

    test('converts T to 10 for display', () => {
      const { container } = render(<Card rank="T" suit="h" />);
      expect(container.textContent).toContain('10');
    });

    test('displays number ranks correctly', () => {
      const { container } = render(<Card rank="7" suit="c" />);
      expect(container.textContent).toContain('7');
    });
  });

  describe('Face-down cards', () => {
    test('renders face-down card with correct aria-label', () => {
      render(<Card rank="A" suit="s" faceDown />);
      expect(screen.getByRole('img')).toHaveAttribute('aria-label', 'Face-down card');
    });

    test('does not show rank or suit when face down', () => {
      const { container } = render(<Card rank="A" suit="s" faceDown />);
      expect(container.textContent).not.toContain('A');
      expect(container.textContent).not.toContain('♠');
    });
  });

  describe('Card sizes', () => {
    test('renders small card', () => {
      const { container } = render(<Card rank="5" suit="h" size="sm" />);
      expect(container.firstChild).toHaveClass('w-12', 'h-16');
    });

    test('renders medium card (default)', () => {
      const { container } = render(<Card rank="5" suit="h" />);
      expect(container.firstChild).toHaveClass('w-16', 'h-22');
    });

    test('renders large card', () => {
      const { container } = render(<Card rank="5" suit="h" size="lg" />);
      expect(container.firstChild).toHaveClass('w-24', 'h-32');
    });
  });

  describe('Card interactions', () => {
    test('calls onClick when clicked', () => {
      const handleClick = jest.fn();
      render(<Card rank="A" suit="s" onClick={handleClick} />);
      fireEvent.click(screen.getByRole('img'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('applies highlight animation when highlighted', () => {
      const { container } = render(<Card rank="A" suit="s" highlighted />);
      expect(container.firstChild).toHaveClass('animate-highlight');
    });

    test('applies deal animation when animate is true', () => {
      const { container } = render(<Card rank="A" suit="s" animate />);
      expect(container.firstChild).toHaveClass('animate-deal');
    });
  });
});

describe('CardGrid Component', () => {
  test('renders multiple cards', () => {
    const cards = [
      { rank: 'A', suit: 's' },
      { rank: 'K', suit: 'h' },
    ];
    render(<CardGrid cards={cards} />);
    expect(screen.getByLabelText('A of spades')).toBeInTheDocument();
    expect(screen.getByLabelText('K of hearts')).toBeInTheDocument();
  });

  test('renders all cards face down when faceDown is true', () => {
    const cards = [
      { rank: 'A', suit: 's' },
      { rank: 'K', suit: 'h' },
    ];
    render(<CardGrid cards={cards} faceDown />);
    const faceDownCards = screen.getAllByLabelText('Face-down card');
    expect(faceDownCards).toHaveLength(2);
  });

  test('returns null when cards array is empty', () => {
    const { container } = render(<CardGrid cards={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('returns null when cards is undefined', () => {
    const { container } = render(<CardGrid />);
    expect(container.firstChild).toBeNull();
  });

  test('highlights specific card by index', () => {
    const cards = [
      { rank: 'A', suit: 's' },
      { rank: 'K', suit: 'h' },
      { rank: 'Q', suit: 'd' },
    ];
    const { container } = render(<CardGrid cards={cards} highlightIndex={1} />);
    const cardElements = container.querySelectorAll('[role="img"]');
    expect(cardElements[1]).toHaveClass('animate-highlight');
    expect(cardElements[0]).not.toHaveClass('animate-highlight');
    expect(cardElements[2]).not.toHaveClass('animate-highlight');
  });
});

describe('EmptyCardSlot Component', () => {
  test('renders empty slot', () => {
    const { container } = render(<EmptyCardSlot />);
    expect(container.textContent).toContain('?');
  });

  test('renders with different sizes', () => {
    const { container: sm } = render(<EmptyCardSlot size="sm" />);
    expect(sm.firstChild).toHaveClass('w-12', 'h-16');

    const { container: lg } = render(<EmptyCardSlot size="lg" />);
    expect(lg.firstChild).toHaveClass('w-24', 'h-32');
  });
});

describe('SUITS and RANKS constants', () => {
  test('SUITS has all four suits', () => {
    expect(Object.keys(SUITS)).toEqual(['h', 'd', 'c', 's']);
  });

  test('each suit has symbol, color, and name', () => {
    Object.values(SUITS).forEach((suit) => {
      expect(suit).toHaveProperty('symbol');
      expect(suit).toHaveProperty('color');
      expect(suit).toHaveProperty('name');
    });
  });

  test('RANKS has all 13 ranks', () => {
    expect(Object.keys(RANKS)).toHaveLength(13);
    expect(RANKS['A']).toBe('A');
    expect(RANKS['T']).toBe('10');
    expect(RANKS['2']).toBe('2');
  });
});
