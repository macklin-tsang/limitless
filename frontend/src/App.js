import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Simulation from './pages/Simulation';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Navigation */}
        <nav className="bg-white shadow-md border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center h-16">
              <Link to="/" className="text-xl font-bold text-gray-800">
                Limitless Poker AI
              </Link>
              <div className="flex space-x-4">
                <Link
                  to="/"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md transition-colors font-medium"
                >
                  Simulator
                </Link>
                <Link
                  to="/simulation"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md transition-colors font-medium"
                >
                  Batch Run
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/simulation" element={<Simulation />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;