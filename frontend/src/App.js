import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Training from './pages/Training';
import './App.css';

function NavLink({ to, children }) {
  const location = useLocation();
  const active = location.pathname === to;
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md transition-colors font-medium ${
        active ? 'text-yellow-600 bg-yellow-50' : 'text-gray-600 hover:text-gray-900'
      }`}
    >
      {children}
    </Link>
  );
}

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
                <NavLink to="/">Dashboard</NavLink>
                <NavLink to="/training">Training</NavLink>
                <NavLink to="/simulator">Simulator</NavLink>
              </div>
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/training" element={<Training />} />
          <Route path="/simulator" element={<Home />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
