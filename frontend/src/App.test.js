import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Limitless Poker AI app', () => {
  render(<App />);
  // Should find navigation and home page elements
  const headings = screen.getAllByText(/Limitless Poker AI/i);
  expect(headings.length).toBeGreaterThan(0);
});

test('renders navigation links', () => {
  render(<App />);
  // Use getAllByRole to be more specific about link elements
  expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Play' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Simulation' })).toBeInTheDocument();
});

test('renders home page by default', () => {
  render(<App />);
  // Home page should show the Play vs Agent button
  expect(screen.getByText('Play vs Agent')).toBeInTheDocument();
  expect(screen.getByText('Run Simulation')).toBeInTheDocument();
});
