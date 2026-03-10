# Limitless

## Overview
Limitless is a No Limit Texas Hold'em AI Agent that simulates heads-up games using explicit game knowledge, Monte Carlo simulation and EV for decisions.

## Tech Stack
- **Backend**: 
  - Python (Flask API + Poker Engine)
  - PyTorch
  - Gymnasium
  - NumPy
- **Frontend**: 
  - React 19 with Tailwind CSS
  - Recharts
  - Axios

## Project Structure
```
limitless/
├── backend-python/
│   ├── app.py              # Flask API wrapper
│   ├── train_rl.py         # DQN training script
│   ├── evaluate_rl.py      # RL agent evaluation
│   ├── requirements.txt    # Python dependencies
│   ├── models/             # Saved DQN model checkpoints
│   ├── metrics/            # Training metrics (JSON)
│   └── engine/
│       ├── game.py         # Poker game engine
│       ├── poker_env.py    # Gymnasium RL environment
│       ├── dqn.py          # Deep Q-Network architecture
│       ├── rl_brain.py     # RL agent decision logic
│       ├── brain.py        # TAG agent decision logic
│       ├── fish_brain.py   # Fish (calling station) agent
│       ├── opponent_model.py # Opponent modeling
│       ├── card.py         # Card class
│       ├── hand_eval.py    # Hand evaluation
│       ├── strength.py     # Hand strength calculations
│       └── simulation.py   # Batch simulation runner
├── frontend/
│   ├── src/
│   │   ├── components/     # React components (Card, PokerTable)
│   │   ├── pages/          # Home, Simulation, Training, Dashboard
│   │   └── services/       # API client
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+

### Backend Setup
```bash
cd backend-python
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5000
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
# Runs on http://localhost:3000
```

## Features

### Agent Types
- **TAG (Tight-Aggressive)**: Plays 20-25% of hands with strong aggression
- **Fish (Calling Station)**: Loose-passive player that calls too often
- **Main Agent**: Uses Monte Carlo simulation for postflop decisions

### Simulation Modes
- **Single Hand**: Watch agents play one hand with full action history
- **Batch Simulation**: Run 10-10,000 hands and view win rate statistics

## API Endpoints

### Python Backend (Port 5000)
- `GET /api/health` - Health check
- `POST /api/simulate` - Run batch simulation
- `POST /api/simulate/single` - Run single hand simulation
