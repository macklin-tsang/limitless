import { useState, useEffect, useCallback, useRef } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, BarChart, Bar,
  ReferenceLine, Area, ComposedChart, Cell,
} from 'recharts';

const API_URL = process.env.REACT_APP_PYTHON_API_URL || 'http://localhost:5001/api';

function Training() {
  // Training config
  const [config, setConfig] = useState({
    algo: 'dqn',
    episodes: 10000,
    opponent: 'fish',
    rewardMode: 'shaped',
    lr: 0.0001,
    seed: 42,
    curriculum: false,
    selfPlay: false,
  });

  // State
  const [metrics, setMetrics] = useState([]);
  const [trainingInfo, setTrainingInfo] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);
  const [evalResults, setEvalResults] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [checkpoints, setCheckpoints] = useState([]);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState('dqn_best');
  const pollingRef = useRef(null);
  const sseRef = useRef(null);

  // Check initial status
  useEffect(() => {
    checkStatus();
    fetchCheckpoints();
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (sseRef.current) sseRef.current.close();
    };
  }, []);

  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/training/status`);
      const data = await res.json();
      setIsRunning(data.running);
      if (data.metrics && data.metrics.metrics) {
        setMetrics(data.metrics.metrics);
        setTrainingInfo(data.metrics);
      }
      if (data.running) {
        startPolling();
      }
    } catch (err) {
      // Backend not running
    }
  };

  const fetchCheckpoints = async () => {
    try {
      const res = await fetch(`${API_URL}/training/checkpoints`);
      const data = await res.json();
      setCheckpoints(data.checkpoints || []);
    } catch (err) {
      // Ignore
    }
  };

  const startPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/training/status`);
        const data = await res.json();

        if (data.metrics && data.metrics.metrics) {
          setMetrics(data.metrics.metrics);
          setTrainingInfo(data.metrics);
        }

        if (!data.running) {
          setIsRunning(false);
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          fetchCheckpoints();
        }
      } catch (err) {
        // Ignore polling errors
      }
    }, 2000);
  }, []);

  const startTraining = async () => {
    setError(null);
    setMetrics([]);
    setTrainingInfo(null);

    try {
      const res = await fetch(`${API_URL}/training/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          algo: config.algo,
          episodes: config.episodes,
          opponent: config.opponent,
          reward_mode: config.rewardMode,
          lr: config.lr,
          seed: config.seed,
          curriculum: config.curriculum,
          self_play: config.selfPlay,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to start training');
      }

      const data = await res.json();
      setIsRunning(true);
      setTrainingInfo(data);
      startPolling();
    } catch (err) {
      setError(err.message);
    }
  };

  const stopTraining = async () => {
    try {
      await fetch(`${API_URL}/training/stop`, { method: 'POST' });
      setIsRunning(false);
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      fetchCheckpoints();
    } catch (err) {
      setError(err.message);
    }
  };

  const runEvaluation = async (opponent) => {
    setEvalLoading(true);
    setEvalResults(null);
    try {
      const res = await fetch(`${API_URL}/training/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          checkpoint: selectedCheckpoint,
          opponent,
          games: 500,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Evaluation failed');
      }
      const data = await res.json();
      setEvalResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setEvalLoading(false);
    }
  };

  const reloadAgent = async () => {
    try {
      const res = await fetch(`${API_URL}/training/reload-rl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ checkpoint: selectedCheckpoint }),
      });
      const data = await res.json();
      if (data.status === 'loaded') {
        setError(null);
        alert(`RL Agent loaded from ${selectedCheckpoint}. Available as "RL" agent type in Dashboard.`);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? Number(value) : value,
    }));
  };

  // Derived data
  const latestMetric = metrics.length > 0 ? metrics[metrics.length - 1] : null;

  // Downsample for charts if too many points
  const chartData = metrics.length > 500
    ? metrics.filter((_, i) => i % Math.ceil(metrics.length / 500) === 0)
    : metrics;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-[1400px] mx-auto">
        {/* Header + Training Config */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">RL Training Lab</h1>
              <p className="text-sm text-gray-500">Train, monitor, and evaluate reinforcement learning poker agents</p>
            </div>
            {isRunning && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium text-green-700">Training Active</span>
              </div>
            )}
          </div>

          <div className="mt-4 flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Algorithm</label>
              <select name="algo" value={config.algo} onChange={handleChange}
                className="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="dqn">DQN (Double DQN)</option>
                <option value="ppo">PPO (SB3)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Episodes</label>
              <input type="number" name="episodes" value={config.episodes} onChange={handleChange}
                min={100} max={200000}
                className="w-28 bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Opponent</label>
              <select name="opponent" value={config.opponent} onChange={handleChange}
                className="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="fish">Fish (Easy)</option>
                <option value="tag">TAG (Hard)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Reward</label>
              <select name="rewardMode" value={config.rewardMode} onChange={handleChange}
                className="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="shaped">Shaped</option>
                <option value="simple">Simple</option>
                <option value="normalized">Normalized</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">LR</label>
              <input type="number" name="lr" value={config.lr} onChange={handleChange}
                step={0.00001} min={0.000001}
                className="w-28 bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Seed</label>
              <input type="number" name="seed" value={config.seed} onChange={handleChange}
                className="w-20 bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div className="flex gap-3">
              <label className="flex items-center gap-1.5 text-sm text-gray-600">
                <input type="checkbox" name="curriculum" checked={config.curriculum} onChange={handleChange}
                  className="rounded" />
                Curriculum
              </label>
              <label className="flex items-center gap-1.5 text-sm text-gray-600">
                <input type="checkbox" name="selfPlay" checked={config.selfPlay} onChange={handleChange}
                  className="rounded" />
                Self-Play
              </label>
            </div>
            <div className="flex gap-2">
              {!isRunning ? (
                <button onClick={startTraining}
                  className="px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white font-bold rounded-lg transition-colors">
                  Start Training
                </button>
              ) : (
                <button onClick={stopTraining}
                  className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg transition-colors">
                  Stop Training
                </button>
              )}
            </div>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
        </div>

        {/* KPI Cards */}
        {latestMetric && (
          <div className="grid grid-cols-6 gap-4 mb-6">
            <KpiCard label="Episode" value={latestMetric.episode} />
            <KpiCard label="Avg Reward (100)" value={latestMetric.avg_reward_100}
              highlight={latestMetric.avg_reward_100 > 0} />
            <KpiCard label="Win Rate" value={`${(latestMetric.win_rate * 100).toFixed(1)}%`}
              highlight={latestMetric.win_rate > 0.5} />
            <KpiCard label="Epsilon" value={latestMetric.epsilon} />
            <KpiCard label="Loss" value={latestMetric.loss.toFixed(5)} />
            <KpiCard label="Wall Time" value={formatTime(latestMetric.wall_time_seconds)} />
          </div>
        )}

        {/* Charts Grid */}
        {chartData.length > 0 && (
          <div className="grid grid-cols-12 gap-6 mb-6">
            {/* Reward Over Time */}
            <div className="col-span-8 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Avg Reward (100 episode window)</h2>
              <p className="text-xs text-gray-400 mb-3">Higher is better - agent profitability over training</p>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="episode" tick={{ fontSize: 11 }}
                    label={{ value: 'Episode', position: 'insideBottom', offset: -3, fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 11 }}
                    label={{ value: 'Reward (BB)', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                  <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="4 4" />
                  <Tooltip content={<MetricsTooltip />} />
                  <Legend />
                  <Area type="monotone" dataKey="avg_reward_100" name="Avg Reward (100)"
                    stroke="#2563eb" fill="#2563eb" fillOpacity={0.08} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="episode_reward" name="Episode Reward"
                    stroke="#d1d5db" strokeWidth={0.5} dot={false} opacity={0.4} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Win Rate Over Time */}
            <div className="col-span-4 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Win Rate</h2>
              <p className="text-xs text-gray-400 mb-3">Running win rate over training</p>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="episode" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                  <ReferenceLine y={0.5} stroke="#9ca3af" strokeDasharray="4 4" />
                  <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
                  <Line type="monotone" dataKey="win_rate" name="Win Rate"
                    stroke="#22c55e" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Loss Over Time */}
            <div className="col-span-6 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Training Loss</h2>
              <p className="text-xs text-gray-400 mb-3">DQN loss (lower is better convergence)</p>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="episode" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="loss" name="Loss"
                    stroke="#ef4444" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Epsilon Decay */}
            <div className="col-span-6 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Exploration (Epsilon)</h2>
              <p className="text-xs text-gray-400 mb-3">Decays from random to greedy over training</p>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="episode" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="epsilon" name="Epsilon"
                    stroke="#8b5cf6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* No data state */}
        {metrics.length === 0 && !isRunning && (
          <div className="text-center text-gray-400 py-12 text-lg bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
            Configure training parameters and click Start Training to begin
          </div>
        )}

        {/* Evaluation & Checkpoints */}
        <div className="grid grid-cols-12 gap-6">
          {/* Evaluation Panel */}
          <div className="col-span-7 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Evaluate Trained Agent</h2>
            <div className="flex items-end gap-3 mb-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Checkpoint</label>
                <select value={selectedCheckpoint} onChange={(e) => setSelectedCheckpoint(e.target.value)}
                  className="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  {checkpoints.length > 0 ? (
                    checkpoints.map(cp => (
                      <option key={cp.name} value={cp.name}>{cp.name} ({cp.size_mb}MB)</option>
                    ))
                  ) : (
                    <option value="dqn_best">dqn_best (default)</option>
                  )}
                </select>
              </div>
              <button onClick={() => runEvaluation('fish')} disabled={evalLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-300 text-white text-sm font-medium rounded-lg">
                vs Fish
              </button>
              <button onClick={() => runEvaluation('tag')} disabled={evalLoading}
                className="px-4 py-2 bg-orange-500 hover:bg-orange-400 disabled:bg-gray-300 text-white text-sm font-medium rounded-lg">
                vs TAG
              </button>
              <button onClick={() => runEvaluation('random')} disabled={evalLoading}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-300 text-white text-sm font-medium rounded-lg">
                vs Random
              </button>
              <button onClick={reloadAgent}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg">
                Load to Dashboard
              </button>
            </div>

            {evalLoading && (
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent" />
                Evaluating...
              </div>
            )}

            {evalResults && (
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Opponent</p>
                    <p className="font-bold text-gray-900 capitalize">{evalResults.opponent}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Games</p>
                    <p className="font-bold text-gray-900">{evalResults.games}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Win Rate</p>
                    <p className={`font-bold ${evalResults.win_rate > 50 ? 'text-green-600' : 'text-red-600'}`}>
                      {evalResults.win_rate}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">BB/100</p>
                    <p className={`font-bold ${evalResults.bb_per_100 > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {evalResults.bb_per_100}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">95% CI</p>
                    <p className="font-bold text-gray-900">[{evalResults.ci_low}, {evalResults.ci_high}]</p>
                  </div>
                  <div>
                    <p className="text-gray-500">VPIP</p>
                    <p className="font-bold text-gray-900">{evalResults.vpip}%</p>
                  </div>
                  <div>
                    <p className="text-gray-500">W/L</p>
                    <p className="font-bold text-gray-900">{evalResults.hands_won}W / {evalResults.hands_lost}L</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Total Profit</p>
                    <p className={`font-bold ${evalResults.total_profit_bb > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {evalResults.total_profit_bb > 0 ? '+' : ''}{evalResults.total_profit_bb} BB
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">SD Win %</p>
                    <p className="font-bold text-gray-900">{evalResults.showdown_win_rate}%</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Checkpoints Panel */}
          <div className="col-span-5 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-semibold text-gray-800">Saved Checkpoints</h2>
              <button onClick={fetchCheckpoints}
                className="text-xs text-blue-600 hover:text-blue-500">Refresh</button>
            </div>
            <div className="max-h-[300px] overflow-y-auto">
              {checkpoints.length === 0 ? (
                <p className="text-gray-400 text-sm">No checkpoints yet. Train a model to create checkpoints.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500">
                      <th className="text-left py-2">Name</th>
                      <th className="text-left py-2">Algo</th>
                      <th className="text-right py-2">Size</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-700">
                    {checkpoints.map(cp => (
                      <tr key={cp.filename} className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedCheckpoint(cp.name)}>
                        <td className={`py-2 ${cp.name === selectedCheckpoint ? 'font-bold text-blue-600' : ''}`}>
                          {cp.name}
                        </td>
                        <td className="py-2 uppercase text-xs">{cp.algo}</td>
                        <td className="py-2 text-right">{cp.size_mb} MB</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Sub-components */

function KpiCard({ label, value, sub, highlight }) {
  const formatted = typeof value === 'number' ? (
    Number.isInteger(value) ? value.toLocaleString() : value.toFixed(4)
  ) : value;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-xl font-bold mt-1 ${highlight ? 'text-green-600' : 'text-gray-900'}`}>
        {formatted}
      </p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function MetricsTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-medium text-gray-700 mb-1">Episode {label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">
            {typeof p.value === 'number' ? p.value.toFixed(4) : p.value}
          </span>
        </p>
      ))}
    </div>
  );
}

function formatTime(seconds) {
  if (!seconds) return '0s';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default Training;
