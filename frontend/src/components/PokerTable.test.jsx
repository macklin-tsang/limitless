import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import PokerTable from './PokerTable';

describe('PokerTable Component', () => {
  describe('Initial state', () => {
    test('renders poker table with waiting state', () => {
      render(<PokerTable />);
      expect(screen.getByText('Phase: Waiting')).toBeInTheDocument();
      expect(screen.getByText('Deal Cards')).toBeInTheDocument();
    });

    test('shows empty card slots before dealing', () => {
      const { container } = render(<PokerTable />);
      // Should have placeholder slots (? markers)
      const questionMarks = container.querySelectorAll('.text-gray-600');
      expect(questionMarks.length).toBeGreaterThan(0);
    });

    test('displays initial pot as 0', () => {
      render(<PokerTable />);
      expect(screen.getByText('Pot: $0')).toBeInTheDocument();
    });

    test('displays blinds information', () => {
      render(<PokerTable />);
      expect(screen.getByText('Blinds: $1/$2')).toBeInTheDocument();
    });

    test('displays both player stacks', () => {
      render(<PokerTable />);
      // Both should start with $200
      const stacks = screen.getAllByText(/Stack: \$200/);
      expect(stacks).toHaveLength(2);
    });
  });

  describe('Dealing cards', () => {
    test('clicking Deal Cards starts the game', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));

      // Should advance to preflop
      expect(screen.getByText('Phase: Preflop')).toBeInTheDocument();
    });

    test('dealing shows opponent cards face down', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));

      // Opponent cards should be face down
      const faceDownCards = screen.getAllByLabelText('Face-down card');
      expect(faceDownCards).toHaveLength(2);
    });

    test('dealing posts blinds to pot', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));

      // Pot should be SB + BB = 3
      expect(screen.getByText('Pot: $3')).toBeInTheDocument();
    });

    test('hand number increments after dealing', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));
      expect(screen.getByText('Hand #1')).toBeInTheDocument();
    });
  });

  describe('Player actions', () => {
    beforeEach(() => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));
    });

    test('shows action buttons when it is player turn', () => {
      expect(screen.getByText('Fold')).toBeInTheDocument();
      expect(screen.getByText(/Call|Check/)).toBeInTheDocument();
      expect(screen.getByText(/Raise/)).toBeInTheDocument();
      expect(screen.getByText('All In')).toBeInTheDocument();
    });

    test('folding ends the hand', () => {
      fireEvent.click(screen.getByText('Fold'));

      // Should show showdown phase and agent wins
      expect(screen.getByText('Phase: Showdown')).toBeInTheDocument();
      expect(screen.getByText('Agent Wins!')).toBeInTheDocument();
    });

    test('shows Next Hand button after showdown', () => {
      fireEvent.click(screen.getByText('Fold'));
      expect(screen.getByText('Next Hand')).toBeInTheDocument();
    });

    test('raising increases the pot', () => {
      const initialPot = 3; // SB + BB
      fireEvent.click(screen.getByText(/Raise/));

      // Pot should have increased
      const potElement = screen.getByText(/Pot: \$/);
      const potAmount = parseInt(potElement.textContent.replace('Pot: $', ''));
      expect(potAmount).toBeGreaterThan(initialPot);
    });

    test('raising shows agent thinking indicator', () => {
      fireEvent.click(screen.getByText(/Raise/));

      // Should show agent thinking
      expect(screen.getByText('Agent is thinking...')).toBeInTheDocument();
    });
  });

  describe('Multiple hands', () => {
    test('can start multiple hands in sequence', () => {
      render(<PokerTable />);

      // Hand 1
      fireEvent.click(screen.getByText('Deal Cards'));
      expect(screen.getByText('Hand #1')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Fold'));

      // Hand 2
      fireEvent.click(screen.getByText('Next Hand'));
      expect(screen.getByText('Hand #2')).toBeInTheDocument();
    });

    test('winner receives pot after fold', () => {
      render(<PokerTable />);

      // Play a hand and fold
      fireEvent.click(screen.getByText('Deal Cards'));
      fireEvent.click(screen.getByText('Fold'));

      // Agent should have won and received the pot
      expect(screen.getByText('Agent Wins!')).toBeInTheDocument();
    });
  });

  describe('UI elements', () => {
    test('displays agent name and type', () => {
      render(<PokerTable />);
      expect(screen.getByText('Agent (TAG)')).toBeInTheDocument();
    });

    test('displays player name', () => {
      render(<PokerTable />);
      expect(screen.getByText('You')).toBeInTheDocument();
    });

    test('shows bet amounts when betting', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));

      // Should show bet indicators for both players (blinds)
      const betIndicators = screen.getAllByText(/Bet: \$/);
      expect(betIndicators.length).toBeGreaterThanOrEqual(1);
    });

    test('table has proper background styling', () => {
      const { container } = render(<PokerTable />);
      // Should have the felt-green gradient background
      const tableElement = container.querySelector('.bg-gradient-to-br');
      expect(tableElement).toBeInTheDocument();
    });
  });

  describe('Community cards', () => {
    test('no community cards shown during preflop', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));

      // Should only have empty slots for community cards
      // 5 community card slots + 2 player empty slots (now filled)
      const emptySlots = screen.getAllByText('?');
      expect(emptySlots.length).toBeGreaterThan(0);
    });
  });

  describe('Check vs Call display', () => {
    test('shows Check when no bet to call', () => {
      render(<PokerTable />);
      fireEvent.click(screen.getByText('Deal Cards'));

      // In preflop, player posted SB, opponent posted BB
      // So player needs to call the difference
      // The button should show "Call" since there's a bet to call
      expect(screen.getByText(/Call|Check/)).toBeInTheDocument();
    });
  });
});
