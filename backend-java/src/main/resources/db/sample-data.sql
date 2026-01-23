-- Sample Data for Poker Agent Application
-- Database: poker_agent
--
-- This script inserts sample data for testing and development purposes.
-- Run this after schema.sql has been executed.
--
-- Usage: \i sample-data.sql

-- Clear existing data (optional, comment out if appending)
DELETE FROM game_results;
DELETE FROM users;

-- Reset sequences
ALTER SEQUENCE users_id_seq RESTART WITH 1;
ALTER SEQUENCE game_results_id_seq RESTART WITH 1;

-- Insert sample users
INSERT INTO users (username, email) VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('diana', 'diana@example.com'),
    ('demo_user', 'demo@pokeragent.com');

-- Insert sample game results for alice (user_id = 1)
-- Simulating a mix of wins and losses against different opponents
INSERT INTO game_results (user_id, agent_name, opponent_name, result, profit, hands_played, timestamp) VALUES
    (1, 'TAG Bot', 'Random Bot', 'win', 125.50, 100, NOW() - INTERVAL '7 days'),
    (1, 'TAG Bot', 'Random Bot', 'win', 87.25, 100, NOW() - INTERVAL '6 days'),
    (1, 'TAG Bot', 'LAG Bot', 'loss', -45.00, 100, NOW() - INTERVAL '5 days'),
    (1, 'TAG Bot', 'Rock Bot', 'win', 62.75, 100, NOW() - INTERVAL '4 days'),
    (1, 'LAG Bot', 'Random Bot', 'win', 156.00, 100, NOW() - INTERVAL '3 days'),
    (1, 'LAG Bot', 'TAG Bot', 'loss', -32.50, 100, NOW() - INTERVAL '2 days'),
    (1, 'TAG Bot', 'Calling Station', 'win', 210.25, 150, NOW() - INTERVAL '1 day'),
    (1, 'TAG Bot', 'Random Bot', 'win', 95.00, 100, NOW());

-- Insert sample game results for bob (user_id = 2)
INSERT INTO game_results (user_id, agent_name, opponent_name, result, profit, hands_played, timestamp) VALUES
    (2, 'LAG Bot', 'Random Bot', 'win', 178.50, 100, NOW() - INTERVAL '5 days'),
    (2, 'LAG Bot', 'TAG Bot', 'win', 45.25, 100, NOW() - INTERVAL '4 days'),
    (2, 'Rock Bot', 'LAG Bot', 'loss', -89.00, 100, NOW() - INTERVAL '3 days'),
    (2, 'TAG Bot', 'Calling Station', 'win', 134.75, 100, NOW() - INTERVAL '2 days'),
    (2, 'TAG Bot', 'Random Bot', 'win', 112.00, 100, NOW() - INTERVAL '1 day');

-- Insert sample game results for charlie (user_id = 3)
INSERT INTO game_results (user_id, agent_name, opponent_name, result, profit, hands_played, timestamp) VALUES
    (3, 'Rock Bot', 'Random Bot', 'win', 45.00, 100, NOW() - INTERVAL '3 days'),
    (3, 'Rock Bot', 'LAG Bot', 'loss', -78.50, 100, NOW() - INTERVAL '2 days'),
    (3, 'TAG Bot', 'Random Bot', 'win', 156.25, 150, NOW() - INTERVAL '1 day');

-- Insert sample game results for demo_user (user_id = 5)
-- More comprehensive data for demonstration purposes
INSERT INTO game_results (user_id, agent_name, opponent_name, result, profit, hands_played, timestamp) VALUES
    (5, 'TAG Bot', 'Random Bot', 'win', 234.50, 200, NOW() - INTERVAL '14 days'),
    (5, 'TAG Bot', 'Random Bot', 'win', 189.25, 200, NOW() - INTERVAL '13 days'),
    (5, 'TAG Bot', 'LAG Bot', 'loss', -67.00, 200, NOW() - INTERVAL '12 days'),
    (5, 'TAG Bot', 'LAG Bot', 'win', 45.50, 200, NOW() - INTERVAL '11 days'),
    (5, 'LAG Bot', 'Random Bot', 'win', 312.75, 200, NOW() - INTERVAL '10 days'),
    (5, 'LAG Bot', 'Rock Bot', 'win', 156.00, 200, NOW() - INTERVAL '9 days'),
    (5, 'LAG Bot', 'TAG Bot', 'loss', -89.25, 200, NOW() - INTERVAL '8 days'),
    (5, 'Rock Bot', 'Random Bot', 'win', 78.50, 200, NOW() - INTERVAL '7 days'),
    (5, 'Rock Bot', 'Calling Station', 'win', 134.25, 200, NOW() - INTERVAL '6 days'),
    (5, 'TAG Bot', 'Calling Station', 'win', 267.00, 200, NOW() - INTERVAL '5 days'),
    (5, 'TAG Bot', 'Random Bot', 'win', 145.75, 200, NOW() - INTERVAL '4 days'),
    (5, 'TAG Bot', 'LAG Bot', 'draw', 0.00, 200, NOW() - INTERVAL '3 days'),
    (5, 'LAG Bot', 'Calling Station', 'win', 289.50, 200, NOW() - INTERVAL '2 days'),
    (5, 'TAG Bot', 'Rock Bot', 'win', 112.25, 200, NOW() - INTERVAL '1 day'),
    (5, 'TAG Bot', 'Random Bot', 'win', 178.00, 200, NOW());

-- Verify data insertion
SELECT 'Users inserted:' AS info, COUNT(*) AS count FROM users;
SELECT 'Game results inserted:' AS info, COUNT(*) AS count FROM game_results;

-- Sample queries to verify data integrity

-- Query 1: Get user statistics summary
SELECT
    u.username,
    COUNT(gr.id) AS total_games,
    SUM(CASE WHEN gr.result = 'win' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN gr.result = 'loss' THEN 1 ELSE 0 END) AS losses,
    ROUND(SUM(gr.profit)::numeric, 2) AS total_profit,
    SUM(gr.hands_played) AS total_hands
FROM users u
LEFT JOIN game_results gr ON u.id = gr.user_id
GROUP BY u.id, u.username
ORDER BY total_profit DESC;

-- Query 2: Agent performance comparison
SELECT
    agent_name,
    COUNT(*) AS games_played,
    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_rate,
    ROUND(SUM(profit)::numeric, 2) AS total_profit,
    ROUND(AVG(profit)::numeric, 2) AS avg_profit_per_game
FROM game_results
GROUP BY agent_name
ORDER BY win_rate DESC;
