-- PostgreSQL Schema for Poker Agent Application
-- Database: poker_agent
--
-- This script creates the core tables for the poker agent system.
-- Tables are created with proper constraints, indexes, and foreign keys.
--
-- Usage:
--   1. Create database: CREATE DATABASE poker_agent;
--   2. Connect to database: \c poker_agent
--   3. Run this script: \i schema.sql

-- Drop tables if they exist (for clean re-initialization)
DROP TABLE IF EXISTS game_results CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table: stores registered poker players/users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT chk_username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Game results table: stores outcomes of poker games/simulations
CREATE TABLE game_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,
    opponent_name VARCHAR(50) NOT NULL,
    result VARCHAR(10) NOT NULL,
    profit DECIMAL(10, 2) NOT NULL,
    hands_played INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT chk_result_values CHECK (result IN ('win', 'loss', 'draw')),
    CONSTRAINT chk_hands_positive CHECK (hands_played > 0)
);

-- Indexes for common query patterns
CREATE INDEX idx_game_results_user_id ON game_results(user_id);
CREATE INDEX idx_game_results_timestamp ON game_results(timestamp DESC);
CREATE INDEX idx_game_results_agent_name ON game_results(agent_name);
CREATE INDEX idx_users_username ON users(username);

-- Comments for documentation
COMMENT ON TABLE users IS 'Registered users/players in the poker agent system';
COMMENT ON COLUMN users.username IS 'Unique username for login and display';
COMMENT ON COLUMN users.email IS 'User email address for notifications';
COMMENT ON COLUMN users.created_at IS 'Account creation timestamp';

COMMENT ON TABLE game_results IS 'Records of poker game outcomes between agents and opponents';
COMMENT ON COLUMN game_results.agent_name IS 'Name of the AI agent (e.g., TAG Bot, LAG Bot)';
COMMENT ON COLUMN game_results.opponent_name IS 'Name of the opponent (human or AI)';
COMMENT ON COLUMN game_results.result IS 'Game outcome: win, loss, or draw';
COMMENT ON COLUMN game_results.profit IS 'Net profit/loss in big blinds or chips';
COMMENT ON COLUMN game_results.hands_played IS 'Number of hands played in the session';
