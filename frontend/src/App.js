import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Simulation from './pages/Simulation';
import PokerTable from './components/PokerTable';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-900">
        {/* Navigation */}
        <nav className="bg-gray-800 shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center h-16">
              <Link to="/" className="text-xl font-bold text-white">
                Limitless Poker AI
              </Link>
              <div className="flex space-x-4">
                <Link
                  to="/"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md transition-colors"
                >
                  Home
                </Link>
                <Link
                  to="/play"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md transition-colors"
                >
                  Play
                </Link>
                <Link
                  to="/simulation"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md transition-colors"
                >
                  Simulation
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/play" element={<PokerTable />} />
          <Route path="/simulation" element={<Simulation />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
