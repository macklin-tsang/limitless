# Limitless

## Overview
Limitless is a No Limit Texas Hold'em AI Agent that simulates heads-up games using explicit game knowledge, Monte Carlo simulation and EV for decisions.

## Tech Stack
- **Backend**: Python (Flask API + Poker Engine)
- **Frontend**: React with Tailwind CSS

## Project Structure
```
limitless/
├── backend-python/
│   ├── app.py              # Flask API wrapper
│   ├── requirements.txt    # Python dependencies
│   └── engine/
│       ├── game.py         # Poker game engine
│       ├── brain.py        # TAG agent decision logic
│       ├── fish_brain.py   # Fish (calling station) agent
│       ├── card.py         # Card class
│       ├── hand_eval.py    # Hand evaluation
│       ├── strength.py     # Hand strength calculations
│       └── simulation.py   # Batch simulation runner
├── frontend/
│   ├── src/
│   │   ├── components/     # React components (Card, PokerTable)
│   │   ├── pages/          # Home and Simulation pages
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
