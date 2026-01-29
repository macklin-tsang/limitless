import { useState, useCallback } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ComposedChart, Area, ReferenceLine, Cell,
} from 'recharts';

const API_URL = process.env.REACT_APP_PYTHON_API_URL || 'http://localhost:5001/api';

function Dashboard() {
  const [config, setConfig] = useState({
    agent1Type: 'TAG',
    agent2Type: 'FISH',
    numHands: 200,
    smallBlind: 5,
    bigBlind: 10,
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedHand, setSelectedHand] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState('agent1');

  const runAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/simulate/analytics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent1_type: config.agent1Type,
          agent2_type: config.agent2Type,
          num_hands: config.numHands,
          small_blind: config.smallBlind,
          big_blind: config.bigBlind,
        }),
      });
      if (!res.ok) throw new Error('Simulation failed');
      const json = await res.json();
      setData(json);
      setSelectedHand(null);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend');
    } finally {
      setLoading(false);
    }
  }, [config]);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setConfig(prev => ({ ...prev, [name]: type === 'number' ? Number(value) : value }));
  };

  const agent = data ? (selectedAgent === 'agent1' ? data.agent1 : data.agent2) : null;
  const otherAgent = data ? (selectedAgent === 'agent1' ? data.agent2 : data.agent1) : null;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-[1400px] mx-auto">
        {/* Header + Config */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Agent Observability Dashboard</h1>
          <div className="flex flex-wrap gap-4 items-end">
            <SelectField label="Agent 1" name="agent1Type" value={config.agent1Type} onChange={handleChange}
              options={[['TAG', 'TAG (Tight-Aggressive)'], ['MAIN', 'Main Agent'], ['FISH', 'Fish']]} />
            <SelectField label="Agent 2" name="agent2Type" value={config.agent2Type} onChange={handleChange}
              options={[['FISH', 'Fish (Calling Station)'], ['TAG', 'TAG'], ['MAIN', 'Main Agent']]} />
            <NumberField label="Hands" name="numHands" value={config.numHands} onChange={handleChange} min={10} max={10000} />
            <NumberField label="SB" name="smallBlind" value={config.smallBlind} onChange={handleChange} min={1} />
            <NumberField label="BB" name="bigBlind" value={config.bigBlind} onChange={handleChange} min={2} />
            <button onClick={runAnalytics} disabled={loading}
              className="px-6 py-2.5 bg-yellow-500 hover:bg-yellow-400 disabled:bg-gray-300 text-gray-900 font-bold rounded-lg transition-colors">
              {loading ? 'Running...' : 'Run Simulation'}
            </button>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
        </div>

        {!data && !loading && (
          <div className="text-center text-gray-400 py-20 text-lg">
            Configure and run a simulation to view analytics
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-yellow-500 border-t-transparent" />
          </div>
        )}

        {data && (
          <>
            {/* Agent Toggle */}
            <div className="flex gap-2 mb-6">
              <button onClick={() => setSelectedAgent('agent1')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedAgent === 'agent1' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'}`}>
                {data.agent1.name}
              </button>
              <button onClick={() => setSelectedAgent('agent2')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedAgent === 'agent2' ? 'bg-orange-500 text-white' : 'bg-white text-gray-700 border border-gray-300'}`}>
                {data.agent2.name}
              </button>
            </div>

            {/* CSS Grid Dashboard */}
            <div className="grid grid-cols-12 gap-6">

              {/* Row 1: KPI Cards */}
              <KpiCard label="Win Rate" value={`${agent.winRate}%`} sub={`${agent.handsWon}W / ${agent.handsLost}L`} highlight={agent.winRate > 50} />
              <KpiCard label="BB/100" value={agent.bbPer100} sub={`CI: [${agent.ciLow}, ${agent.ciHigh}]`} highlight={agent.bbPer100 > 0} />
              <KpiCard label="Total Profit" value={`${agent.totalProfitBB > 0 ? '+' : ''}${agent.totalProfitBB} BB`} highlight={agent.totalProfitBB > 0} />
              <KpiCard label="Std Dev" value={agent.stdDev} sub="per hand (BB)" />
              <KpiCard label="VPIP / PFR" value={`${agent.vpip}% / ${agent.pfr}%`} />
              <KpiCard label="Aggression" value={agent.aggressionFactor} sub={`SD Win: ${agent.showdownWinRate}%`} />

              {/* Row 2: Cumulative Profit/Loss Chart */}
              <div className="col-span-8 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-1">Cumulative Profit / Loss</h2>
                <p className="text-xs text-gray-400 mb-3">Running total of winnings relative to starting stack</p>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={buildProfitData(data)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="hand" tick={{ fontSize: 11 }} label={{ value: 'Hand #', position: 'insideBottom', offset: -3, fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 11 }} label={{ value: 'Profit ($)', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                    <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="4 4" />
                    <Tooltip content={<ProfitTooltip a1={data.agent1.name} a2={data.agent2.name} />} />
                    <Legend />
                    <Area type="monotone" dataKey="agent1Cum" name={`${data.agent1.name} cumulative`} stroke="#2563eb" fill="#2563eb" fillOpacity={0.08} strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="agent2Cum" name={`${data.agent2.name} cumulative`} stroke="#f97316" fill="#f97316" fillOpacity={0.08} strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              {/* Per-Hand Win/Loss Bar Chart */}
              <div className="col-span-4 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-1">Per-Hand Result</h2>
                <p className="text-xs text-gray-400 mb-3">{agent.name} - win (green) / loss (red)</p>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={buildPerHandData(data, selectedAgent)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="hand" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                    <YAxis tick={{ fontSize: 11 }} label={{ value: '$', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                    <ReferenceLine y={0} stroke="#9ca3af" />
                    <Tooltip formatter={(v) => `$${v.toFixed(2)}`} />
                    <Bar dataKey="delta" name="Hand P/L">
                      {buildPerHandData(data, selectedAgent).map((entry, i) => (
                        <Cell key={i} fill={entry.delta >= 0 ? '#22c55e' : '#ef4444'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Win Rate Bar Chart */}
              <div className="col-span-4 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Win Rate Comparison</h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[
                    { stat: 'Win %', [data.agent1.name]: data.agent1.winRate, [data.agent2.name]: data.agent2.winRate },
                    { stat: 'SD Win %', [data.agent1.name]: data.agent1.showdownWinRate, [data.agent2.name]: data.agent2.showdownWinRate },
                    { stat: 'VPIP', [data.agent1.name]: data.agent1.vpip, [data.agent2.name]: data.agent2.vpip },
                    { stat: 'PFR', [data.agent1.name]: data.agent1.pfr, [data.agent2.name]: data.agent2.pfr },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="stat" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey={data.agent1.name} fill="#2563eb" radius={[4,4,0,0]} />
                    <Bar dataKey={data.agent2.name} fill="#f97316" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Row 3: BB/100 Stats Table */}
              <div className="col-span-6 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Performance Table</h2>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500">
                      <th className="text-left py-2">Metric</th>
                      <th className="text-right py-2">{data.agent1.name}</th>
                      <th className="text-right py-2">{data.agent2.name}</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-800">
                    {[
                      ['Hands Played', data.numHands, data.numHands],
                      ['Hands Won', data.agent1.handsWon, data.agent2.handsWon],
                      ['Win Rate', `${data.agent1.winRate}%`, `${data.agent2.winRate}%`],
                      ['BB/100', data.agent1.bbPer100, data.agent2.bbPer100],
                      ['Total Profit (BB)', data.agent1.totalProfitBB, data.agent2.totalProfitBB],
                      ['Std Dev (BB)', data.agent1.stdDev, data.agent2.stdDev],
                      ['95% CI (BB/100)', `[${data.agent1.ciLow}, ${data.agent1.ciHigh}]`, `[${data.agent2.ciLow}, ${data.agent2.ciHigh}]`],
                      ['Showdown Win %', `${data.agent1.showdownWinRate}%`, `${data.agent2.showdownWinRate}%`],
                      ['VPIP', `${data.agent1.vpip}%`, `${data.agent2.vpip}%`],
                      ['PFR', `${data.agent1.pfr}%`, `${data.agent2.pfr}%`],
                      ['Aggression Factor', data.agent1.aggressionFactor, data.agent2.aggressionFactor],
                    ].map(([label, v1, v2], i) => (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-2 font-medium">{label}</td>
                        <td className="py-2 text-right">{v1}</td>
                        <td className="py-2 text-right">{v2}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Radar Chart */}
              <div className="col-span-6 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Behavioral Fingerprint</h2>
                <ResponsiveContainer width="100%" height={320}>
                  <RadarChart data={buildRadarData(data)}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
                    <Radar name={data.agent1.name} dataKey="agent1" stroke="#2563eb" fill="#2563eb" fillOpacity={0.2} />
                    <Radar name={data.agent2.name} dataKey="agent2" stroke="#f97316" fill="#f97316" fillOpacity={0.2} />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Row 4: Action Distribution Stacked Bars */}
              <div className="col-span-7 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-1">
                  Action Distribution by Street
                  <span className="text-sm font-normal text-gray-500 ml-2">({agent.name})</span>
                </h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={buildActionData(agent)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                    <YAxis type="category" dataKey="street" tick={{ fontSize: 12 }} width={60} />
                    <Tooltip formatter={(v) => `${v}%`} />
                    <Legend />
                    <Bar dataKey="fold" stackId="a" fill="#ef4444" name="Fold" />
                    <Bar dataKey="call" stackId="a" fill="#3b82f6" name="Call" />
                    <Bar dataKey="raise" stackId="a" fill="#f59e0b" name="Raise" />
                    <Bar dataKey="check" stackId="a" fill="#6b7280" name="Check" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Raise Sizing Distribution */}
              <div className="col-span-5 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-1">
                  Raise Sizing
                  <span className="text-sm font-normal text-gray-500 ml-2">({agent.name})</span>
                </h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={buildRaiseSizingData(agent)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[4,4,0,0]} name="Count" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Row 5: Hand History Replay */}
              <div className="col-span-12 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Hand History Replay</h2>
                <div className="flex gap-6">
                  {/* Hand List */}
                  <div className="w-72 shrink-0 border-r border-gray-200 pr-4 max-h-[400px] overflow-y-auto">
                    <div className="space-y-1">
                      {data.hands.map((hand) => (
                        <button key={hand.handNumber}
                          onClick={() => setSelectedHand(hand)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                            selectedHand?.handNumber === hand.handNumber
                              ? 'bg-blue-50 border border-blue-300 text-blue-800'
                              : 'hover:bg-gray-50 text-gray-700'
                          }`}>
                          <div className="flex justify-between">
                            <span className="font-medium">Hand #{hand.handNumber}</span>
                            <span className={hand.winner === data.agent1.name ? 'text-blue-600' : 'text-orange-500'}>
                              {hand.winner === data.agent1.name ? data.agent1.name : data.agent2.name}
                            </span>
                          </div>
                          <div className="text-xs text-gray-500 mt-0.5">
                            {hand.description} - ${hand.amountWon}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Hand Detail */}
                  <div className="flex-1 min-h-[400px]">
                    {selectedHand ? (
                      <HandReplay hand={selectedHand} agent1Name={data.agent1.name} agent2Name={data.agent2.name} />
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        Select a hand from the list to replay
                      </div>
                    )}
                  </div>
                </div>
              </div>

            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ---------- Sub-components ---------- */

function KpiCard({ label, value, sub, highlight }) {
  return (
    <div className="col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${highlight ? 'text-green-600' : 'text-gray-900'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function SelectField({ label, name, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <select name={name} value={value} onChange={onChange}
        className="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-300">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}

function NumberField({ label, name, value, onChange, min, max }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <input type="number" name={name} value={value} onChange={onChange} min={min} max={max}
        className="w-24 bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-300" />
    </div>
  );
}

function HandReplay({ hand, agent1Name, agent2Name }) {
  const annotated = parseHandActions(hand.actionHistory);

  return (
    <div>
      <div className="flex gap-6 mb-4">
        <div>
          <p className="text-xs text-gray-500 uppercase">{agent1Name}</p>
          <p className="font-mono text-lg">{hand.agent1Cards.join(' ')}</p>
          <p className="text-sm text-gray-600">
            ${hand.agent1StackBefore} &rarr; ${hand.agent1StackAfter}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase">Board</p>
          <p className="font-mono text-lg">{hand.board.length ? hand.board.join(' ') : '-'}</p>
          <p className="text-sm font-semibold text-gray-800 mt-1">{hand.description}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase">{agent2Name}</p>
          <p className="font-mono text-lg">{hand.agent2Cards.join(' ')}</p>
          <p className="text-sm text-gray-600">
            ${hand.agent2StackBefore} &rarr; ${hand.agent2StackAfter}
          </p>
        </div>
      </div>
      <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mb-4 ${
        hand.winner === agent1Name ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
      }`}>
        {hand.winner} wins ${hand.amountWon}
      </div>
      <div className="bg-gray-50 rounded-lg p-4 max-h-[250px] overflow-y-auto">
        <p className="text-xs text-gray-500 uppercase mb-2">Action Log</p>
        <div className="space-y-1">
          {annotated.map((entry, i) => {
            let cls = 'text-gray-700';
            if (entry.type === 'street') cls = 'text-blue-600 font-medium';
            else if (entry.type === 'win') cls = 'text-green-600 font-bold';
            else if (entry.type === 'fold') cls = 'text-red-500';
            else if (entry.type === 'raise') cls = 'text-orange-600';
            if (entry.text.includes('all-in')) cls = 'text-purple-600 font-bold';

            return (
              <div key={i} className="flex items-baseline gap-2">
                {entry.type === 'street' && (
                  <span className="text-xs text-gray-400 font-sans font-semibold whitespace-nowrap">
                    Pot: ${entry.potBefore.toFixed(0)}
                  </span>
                )}
                <p className={`text-sm font-mono ${cls}`}>
                  {entry.text}
                  {entry.sizing && (
                    <span className="ml-2 text-xs font-sans font-semibold text-gray-500 bg-gray-200 px-1.5 py-0.5 rounded">
                      {entry.sizing}
                    </span>
                  )}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function parseHandActions(actionHistory) {
  let pot = 0;
  let currentBet = 0;
  const playerBets = {};
  const result = [];

  for (const action of actionHistory) {
    // Street markers
    if (action.startsWith('FLOP:') || action.startsWith('TURN:') || action.startsWith('RIVER:')) {
      result.push({ text: action, potBefore: pot, type: 'street' });
      currentBet = 0;
      for (const k of Object.keys(playerBets)) playerBets[k] = 0;
      continue;
    }

    // Shows / wins
    if (action.includes(' shows ')) {
      result.push({ text: action, type: 'show' });
      continue;
    }
    if (action.includes(' wins ')) {
      result.push({ text: action, type: 'win' });
      continue;
    }

    // Extract dollar amount
    const dollarMatch = action.match(/\$(\d+\.?\d*)/);
    const amount = dollarMatch ? parseFloat(dollarMatch[1]) : 0;

    // Extract player name (everything before the verb)
    const nameMatch = action.match(/^(.+?)\s+(posts|calls|raises|checks|folds|all-in)/);
    const playerName = nameMatch ? nameMatch[1] : '';

    if (action.includes('posts SB') || action.includes('posts BB')) {
      playerBets[playerName] = amount;
      currentBet = Math.max(currentBet, amount);
      pot += amount;
      result.push({ text: action, type: 'blind' });
    } else if (action.includes('folds')) {
      result.push({ text: action, type: 'fold' });
    } else if (action.includes('checks')) {
      result.push({ text: action, type: 'check' });
    } else if (action.includes('calls')) {
      pot += amount;
      playerBets[playerName] = (playerBets[playerName] || 0) + amount;
      result.push({ text: action, type: 'call' });
    } else if (action.includes('raises')) {
      // "raises to $X" means total committed this round = X
      const prevCommitted = playerBets[playerName] || 0;
      const totalCommit = amount;
      const addedToPot = totalCommit - prevCommitted;
      const callAmount = currentBet - prevCommitted;
      const raiseAmount = totalCommit - currentBet;

      // Pot the raise goes into = pot before action + what they had to call
      const potForSizing = pot + callAmount;

      pot += addedToPot;
      playerBets[playerName] = totalCommit;
      currentBet = totalCommit;

      let sizing = '';
      if (potForSizing > 0 && raiseAmount > 0) {
        const ratio = raiseAmount / potForSizing;
        if (ratio > 1) {
          sizing = `${ratio.toFixed(1)}x overbet`;
        } else {
          sizing = `${Math.round(ratio * 100)}% pot`;
        }
      }
      result.push({ text: action, type: 'raise', sizing });
    } else {
      result.push({ text: action, type: 'other' });
    }
  }

  return result;
}

/* ---------- Data helpers ---------- */

function ProfitTooltip({ active, payload, label, a1, a2 }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-medium text-gray-700 mb-1">Hand #{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">{p.value >= 0 ? '+' : ''}{p.value.toFixed(2)}</span>
        </p>
      ))}
    </div>
  );
}

function buildProfitData(data) {
  const start = data.agent1.bankrollHistory[0];
  const len = Math.max(data.agent1.bankrollHistory.length, data.agent2.bankrollHistory.length);
  const out = [];
  for (let i = 0; i < len; i++) {
    out.push({
      hand: i,
      agent1Cum: data.agent1.bankrollHistory[i] != null ? +(data.agent1.bankrollHistory[i] - start).toFixed(2) : null,
      agent2Cum: data.agent2.bankrollHistory[i] != null ? +(data.agent2.bankrollHistory[i] - start).toFixed(2) : null,
    });
  }
  return out;
}

function buildPerHandData(data, selectedAgent) {
  const history = selectedAgent === 'agent1' ? data.agent1.bankrollHistory : data.agent2.bankrollHistory;
  const out = [];
  for (let i = 1; i < history.length; i++) {
    out.push({
      hand: i,
      delta: +(history[i] - history[i - 1]).toFixed(2),
    });
  }
  return out;
}

function buildRadarData(data) {
  return [
    { metric: 'Win %', agent1: data.agent1.winRate, agent2: data.agent2.winRate },
    { metric: 'VPIP', agent1: data.agent1.vpip, agent2: data.agent2.vpip },
    { metric: 'PFR', agent1: data.agent1.pfr, agent2: data.agent2.pfr },
    { metric: 'Aggression', agent1: Math.min(data.agent1.aggressionFactor * 20, 100), agent2: Math.min(data.agent2.aggressionFactor * 20, 100) },
    { metric: 'SD Win %', agent1: data.agent1.showdownWinRate, agent2: data.agent2.showdownWinRate },
  ];
}

function buildActionData(agent) {
  return ['preflop', 'flop', 'turn', 'river'].map(street => ({
    street: street.charAt(0).toUpperCase() + street.slice(1),
    ...agent.actionDistribution[street],
  }));
}

function buildRaiseSizingData(agent) {
  return Object.entries(agent.raiseSizing).map(([bucket, count]) => ({ bucket, count }));
}

export default Dashboard;
