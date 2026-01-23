import { useState } from 'react';

// API base URL for Python backend
const PYTHON_API_URL = process.env.REACT_APP_PYTHON_API_URL || 'http://localhost:5000/api';

function Simulation() {
  const [config, setConfig] = useState({
    agentType: 'TAG',
    opponentType: 'FISH',
    numGames: 100,
    smallBlind: 5,
    bigBlind: 10,
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value, 10) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`${PYTHON_API_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_type: config.agentType,
          opponent_type: config.opponentType,
          num_games: config.numGames,
          small_blind: config.smallBlind,
          big_blind: config.bigBlind,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to run simulation');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to Python backend. Make sure it is running on port 5000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Batch Simulation</h1>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Configuration Form */}
          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Configuration</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-gray-700 mb-1 font-medium">Agent Type</label>
                <select
                  name="agentType"
                  value={config.agentType}
                  onChange={handleInputChange}
                  className="w-full bg-gray-50 text-gray-800 rounded-lg p-3 border border-gray-300 focus:border-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-200"
                >
                  <option value="TAG">TAG (Tight-Aggressive)</option>
                  <option value="MAIN">Main Agent</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-700 mb-1 font-medium">Opponent Type</label>
                <select
                  name="opponentType"
                  value={config.opponentType}
                  onChange={handleInputChange}
                  className="w-full bg-gray-50 text-gray-800 rounded-lg p-3 border border-gray-300 focus:border-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-200"
                >
                  <option value="FISH">Fish (Calling Station)</option>
                  <option value="TAG">TAG</option>
                  <option value="MAIN">Main Agent</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-700 mb-1 font-medium">Number of Hands</label>
                <input
                  type="number"
                  name="numGames"
                  value={config.numGames}
                  onChange={handleInputChange}
                  min="10"
                  max="10000"
                  className="w-full bg-gray-50 text-gray-800 rounded-lg p-3 border border-gray-300 focus:border-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 mb-1 font-medium">Small Blind</label>
                  <input
                    type="number"
                    name="smallBlind"
                    value={config.smallBlind}
                    onChange={handleInputChange}
                    min="1"
                    className="w-full bg-gray-50 text-gray-800 rounded-lg p-3 border border-gray-300 focus:border-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-200"
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-1 font-medium">Big Blind</label>
                  <input
                    type="number"
                    name="bigBlind"
                    value={config.bigBlind}
                    onChange={handleInputChange}
                    min="2"
                    className="w-full bg-gray-50 text-gray-800 rounded-lg p-3 border border-gray-300 focus:border-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-200"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-yellow-500 hover:bg-yellow-400 disabled:bg-gray-400 text-gray-900 font-bold rounded-lg transition-colors"
              >
                {loading ? 'Running Simulation...' : 'Run Simulation'}
              </button>
            </form>
          </div>

          {/* Results Display */}
          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Results</h2>

            {loading && (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-yellow-500 border-t-transparent"></div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-700">
                {error}
              </div>
            )}

            {results && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <StatCard label="Agent" value={results.agentName} />
                  <StatCard label="Opponent" value={results.opponentName} />
                  <StatCard label="Wins" value={results.wins} />
                  <StatCard label="Losses" value={results.losses} />
                  <StatCard
                    label="Win Rate"
                    value={`${(results.winRate * 100).toFixed(1)}%`}
                    highlight={results.winRate > 0.5}
                  />
                  <StatCard
                    label="Total Profit"
                    value={`${results.totalProfit >= 0 ? '+' : ''}${results.totalProfit.toFixed(2)} BB`}
                    highlight={results.totalProfit > 0}
                  />
                  <StatCard
                    label="Profit/Hand"
                    value={`${results.profitPerHand >= 0 ? '+' : ''}${results.profitPerHand.toFixed(4)} BB`}
                    highlight={results.profitPerHand > 0}
                    colSpan="2"
                  />
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-gray-600 text-sm">
                    {results.wins > results.losses
                      ? 'The agent performed well against this opponent type!'
                      : 'The agent struggled against this opponent. Consider adjusting strategy.'}
                  </p>
                </div>
              </div>
            )}

            {!loading && !error && !results && (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <p>Configure and run a simulation to see results</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, highlight = false, colSpan = '1' }) {
  return (
    <div
      className={`bg-gray-50 rounded-lg p-4 border border-gray-200 ${colSpan === '2' ? 'col-span-2' : ''}`}
    >
      <p className="text-gray-500 text-sm">{label}</p>
      <p
        className={`text-2xl font-bold ${highlight ? 'text-green-600' : 'text-gray-800'}`}
      >
        {value}
      </p>
    </div>
  );
}

export default Simulation;