import { useState, useEffect, useRef } from 'react';
import { Card } from './ui/components';
import { Radio, Brain, Activity, Zap, Loader2, Info, Network } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { AgentNetworkGraph } from './AgentNetworkGraph';
import { RLAgentMode } from './RLAgentMode';

const AGENT_COLORS = ['#06d6a0', '#118ab2', '#ef476f', '#ffd166', '#8338ec'];

export const SignalsTab = ({ signals, eventConfig }) => {
  // Mode: 'webster' | 'rl' | 'marl'
  const [mode, setMode] = useState('webster');
  const [rlStatus, setRlStatus] = useState({ model_exists: false });
  const [rlSession, setRlSession] = useState(null);
  const [rlMetrics, setRlMetrics] = useState({ history: [] });
  const [isStepping, setIsStepping] = useState(false);
  const [isStartingRL, setIsStartingRL] = useState(false);

  // MARL state
  const [marlStatus, setMarlStatus] = useState({ model_exists: false });
  const [marlSession, setMarlSession] = useState(null);
  const [marlMetrics, setMarlMetrics] = useState({ history: [] });
  const [isMarlStepping, setIsMarlStepping] = useState(false);
  const [isStartingMARL, setIsStartingMARL] = useState(false);
  const [engineType, setEngineType] = useState(null);

  const timerRef = useRef(null);
  const marlTimerRef = useRef(null);

  useEffect(() => {
    // Check if AI model is available
    fetch('http://localhost:8000/api/ai/status')
      .then(res => res.json())
      .then(data => {
        if (data.model_exists) setMarlStatus(data);
      })
      .catch(() => { });
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (marlTimerRef.current) clearInterval(marlTimerRef.current);
    };
  }, []);

  const startRLSession = async () => {
    setIsStartingRL(true);
    try {
      const response = await fetch('http://localhost:8000/api/rl/start-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: eventConfig?.latitude || 12.9789,
          longitude: eventConfig?.longitude || 77.5998,
          event_type: eventConfig?.event_type || 'protest',
          duration_hours: eventConfig?.duration_hours || 2.0,
          weather_rain: eventConfig?.weather_rain || false
        })
      });
      const data = await response.json();
      if (data.session_id) {
        setRlSession({
          id: data.session_id,
          step: 0,
          junctions: data.junctions.map(j => ({
            name: j.name,
            green_sec: j.initial_green_sec,
            queue: j.initial_queue,
            adjustment: 0
          }))
        });
        setRlMetrics({ history: [] });
        setIsStepping(true);
      }
    } catch (err) {
      console.error("Error starting RL session:", err);
    } finally {
      setIsStartingRL(false);
    }
  };

  const nextStep = async () => {
    if (!rlSession) return;
    try {
      const response = await fetch('http://localhost:8000/api/rl/next-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: rlSession.id })
      });
      const data = await response.json();

      if (data.actions) {
        setRlSession(prev => ({
          ...prev,
          step: data.step,
          junctions: data.actions.map(a => ({
            name: a.junction,
            green_sec: a.new_green_sec,
            queue: a.queue,
            adjustment: a.adjustment_sec
          }))
        }));

        setRlMetrics(prev => ({
          history: [...prev.history, {
            step: data.step,
            avg_queue: data.metrics.avg_queue,
            reward: data.metrics.reward,
            crowd: data.metrics.crowd_remaining_pct
          }].slice(-30) // keep last 30 steps
        }));

        const totalCars = data.actions.reduce((sum, a) => sum + a.queue, 0);

        if (data.done || (totalCars < 10 && data.metrics.crowd_remaining_pct < 10)) {
          stopAutoStep();
          if (totalCars < 10 && data.metrics.crowd_remaining_pct < 10 && data.step > 0) {
            setTimeout(() => {
              alert("Event Traffic and Crowd Evacuation have been successfully resolved! RL Agent is standing down.");
            }, 300);
          }
        }
      }
    } catch (err) {
      console.error("Error stepping:", err);
      stopAutoStep();
    }
  };

  useEffect(() => {
    let interval = null;
    if (isStepping) {
      interval = setInterval(() => {
        nextStep();
      }, 2000);
      timerRef.current = interval;
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (interval) clearInterval(interval);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isStepping, rlSession?.id]);

  function stopAutoStep() {
    if (timerRef.current) clearInterval(timerRef.current);
    setIsStepping(false);
  }

  const startMARLSession = async () => {
    setIsStartingMARL(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/start-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: eventConfig?.latitude || 12.9789,
          longitude: eventConfig?.longitude || 77.5998,
          event_type: eventConfig?.event_type || 'protest',
          duration_hours: eventConfig?.duration_hours || 2.0,
          weather_rain: eventConfig?.weather_rain || false,
          total_incidents: eventConfig?.total_incidents || 0,
          multi_event_mode: eventConfig?.multi_event_mode || false
        })
      });
      const data = await response.json();
      if (data.session_id) {
        setMarlSession({
          id: data.session_id,
          step: 0,
          agents: data.agents,
          adjacency: data.adjacency,
        });
        setEngineType(data.engine);
        setMarlMetrics({ history: [] });
        setIsMarlStepping(true);
      }
    } catch (err) {
      console.error("Error starting MARL session:", err);
    } finally {
      setIsStartingMARL(false);
    }
  };

  const nextMARLStep = async () => {
    if (!marlSession) return;
    try {
      const response = await fetch('http://localhost:8000/api/ai/next-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: marlSession.id })
      });
      const data = await response.json();
      if (data.agents) {
        setMarlSession(prev => ({
          ...prev,
          step: data.step,
          agents: data.agents,
        }));
        setMarlMetrics(prev => ({
          history: [...prev.history, {
            step: data.step,
            avg_queue: data.global_metrics.avg_queue,
            crowd: data.global_metrics.crowd_remaining_pct,
            total_reward: data.global_metrics.total_reward,
            ...Object.fromEntries(data.agents.map(a => [`q${a.id}`, a.queue])),
          }].slice(-30)
        }));

        const totalCars = data.agents.reduce((s, a) => s + a.queue, 0);
        if (data.done || (totalCars < 10 && data.global_metrics.crowd_remaining_pct < 10)) {
          stopMARLAutoStep();
          if (totalCars < 10 && data.global_metrics.crowd_remaining_pct < 10 && data.step > 0) {
            setTimeout(() => {
              alert("MARL Cooperative Agents have resolved all traffic! Standing down.");
            }, 300);
          }
        }
      }
    } catch (err) {
      console.error("Error stepping MARL:", err);
      stopMARLAutoStep();
    }
  };

  useEffect(() => {
    let interval = null;
    if (isMarlStepping) {
      interval = setInterval(() => { nextMARLStep(); }, 2000);
      marlTimerRef.current = interval;
    } else {
      if (marlTimerRef.current) clearInterval(marlTimerRef.current);
    }
    return () => {
      if (interval) clearInterval(interval);
      if (marlTimerRef.current) clearInterval(marlTimerRef.current);
    };
  }, [isMarlStepping, marlSession?.id]);

  function stopMARLAutoStep() {
    if (marlTimerRef.current) clearInterval(marlTimerRef.current);
    setIsMarlStepping(false);
  }

  if (!signals || signals.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-text-muted)]">
        <Radio size={48} className="mb-4 opacity-50 text-[var(--color-accent)]" />
        <h2 className="text-xl font-bold text-[var(--color-text-main)]">No Signal Data</h2>
        <p>Run analysis to generate adaptive signal timings.</p>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = signals.map(s => ({
    name: s.junction_name.substring(0, 15) + (s.junction_name.length > 15 ? '...' : ''),
    greenMain: s.phase_a_green_sec,
    greenCross: s.phase_b_green_sec,
  }));

  return (
    <div className="flex-1 max-w-6xl mx-auto space-y-6 w-full pb-10">
      <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-4 mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Radio className="text-[var(--color-accent)]" size={28} /> Adaptive Signal Control
          <div className="group relative flex items-center ml-3">
            <div className="flex items-center justify-center transition duration-200 hover:scale-110">
              <Info size={18} className="text-[var(--color-accent)] cursor-help" />
            </div>
            <div className="absolute top-full mt-2 left-0 w-80 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
              When a major event finishes (like a concert), a massive crowd spills out into the surrounding streets, creating a sudden spike in traffic. Traditional traffic lights are static and can't handle this surge. This page demonstrates how an AI agent can take control of the traffic signals in the "Spillover Zone" to flush traffic out efficiently.
            </div>
          </div>
        </h2>

        {(rlStatus.model_exists || marlStatus.model_exists) && (
          <div className="flex bg-[var(--color-base)] p-1 rounded-lg">
            <button
              onClick={() => setMode('webster')}
              className={`px-4 py-2 rounded-md text-sm font-bold flex items-center gap-2 transition-all ${mode === 'webster' ? 'bg-[var(--color-surface-hover)] text-[var(--color-text-main)] shadow' : 'text-[var(--color-text-muted)]'}`}
            >
              <Radio size={16} /> Static (Webster)
            </button>
            {marlStatus.model_exists && (
              <button
                onClick={() => setMode('marl')}
                className={`px-4 py-2 rounded-md text-sm font-bold flex items-center gap-2 transition-all ${mode === 'marl' ? 'bg-[var(--color-accent)] text-black shadow-md' : 'text-[var(--color-text-muted)]'}`}
              >
                <Network size={16} /> Adaptive MARL Agent
              </button>
            )}
          </div>
        )}
      </div>

      {mode === 'webster' ? (
        // --- WEBSTER BASELINE MODE ---
        <>
          <div className="bg-[var(--color-surface-hover)] border-l-4 border-[var(--color-accent)] p-4 rounded-lg mb-6 shadow-xl">
            <h5 className="text-[var(--color-accent)] font-bold uppercase tracking-wider text-xs mb-1">Webster Formula (Baseline)</h5>
            <p className="text-sm text-[var(--color-text-main)]">Static optimization based on predicted flow ratios. Timings are fixed for the duration of the phase.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {signals.map((rec, i) => {
                const green_pct = rec.phase_a_green_sec / rec.cycle_length_sec;
                return (
                  <Card key={i} className="hover:border-[var(--color-accent)] transition-all bg-[var(--color-surface)]">
                    <div className="flex justify-between items-center mb-3">
                      <strong className="text-[var(--color-text-main)] font-bold">{rec.junction_name}</strong>
                      <span className="text-[var(--color-accent)] text-sm font-mono bg-[var(--color-base)] px-2 py-1 rounded">Cycle: {rec.cycle_length_sec}s</span>
                    </div>

                    <div className="flex h-3 rounded overflow-hidden mb-2 shadow-inner">
                      <div style={{ width: `${green_pct * 100}%`, backgroundColor: 'var(--color-accent)' }} className="shadow-lg"></div>
                      <div style={{ width: `${(1 - green_pct) * 100}%`, backgroundColor: 'var(--color-surface-hover)' }} className="shadow-inner"></div>
                    </div>

                    <div className="flex justify-between text-xs text-[var(--color-text-muted)] mb-3 font-mono">
                      <span className="text-[var(--color-text-main)]">Main: {rec.phase_a_green_sec}s</span>
                      <span className="text-[var(--color-text-main)] opacity-70">Cross: {rec.phase_b_green_sec}s</span>
                    </div>

                    <div className="text-sm text-[var(--color-text-main)] bg-[var(--color-base)] p-2 rounded border border-[var(--color-border)]">
                      {rec.recommendation}
                    </div>
                  </Card>
                );
              })}
            </div>

            <div className="relative">
              <div className="sticky top-6">
                <Card className="h-[500px] flex flex-col bg-[var(--color-surface)]">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xs uppercase tracking-widest text-[var(--color-text-muted)] font-bold m-0">Green Split Optimization</h3>
                    <div className="group relative flex items-center z-50">
                      <div className="flex items-center justify-center transition duration-200 hover:scale-110">
                        <Info size={16} className="text-[var(--color-accent)] cursor-help" />
                      </div>
                      <div className="absolute top-full mt-2 right-0 w-64 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
                        <span><strong>Formula:</strong> g<sub>i</sub> = (y<sub>i</sub> / Y) × (C - L)</span><br /><br />
                        Calculates the green time (g_i) for a phase by taking its flow ratio (y_i) over the total intersection flow ratio (Y), multiplied by the cycle length (C) minus lost time (L).
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
                      <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                        <XAxis type="number" stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                        <YAxis dataKey="name" type="category" stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} width={100} />
                        <RechartsTooltip
                          cursor={false}
                          contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                          itemStyle={{ color: 'var(--color-text-main)' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '12px' }} />
                        <Bar dataKey="greenMain" name="Main Route Green (s)" stackId="a" fill="var(--color-accent)" radius={[0, 0, 0, 4]} barSize={24} />
                        <Bar dataKey="greenCross" name="Cross Route Green (s)" stackId="a" fill="rgba(255, 255, 255, 0.4)" radius={[0, 4, 4, 0]} barSize={24} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </>
      ) : engineType === 'Single RL' ? (
        <RLAgentMode
          session={marlSession}
          metrics={marlMetrics}
          isStepping={isMarlStepping}
          isStarting={isStartingMARL}
          onStart={startMARLSession}
          onToggleStepping={() => setIsMarlStepping(!isMarlStepping)}
        />
      ) : (
        // --- MARL COOPERATIVE MODE ---
        <div className="space-y-6 animate-fade-in">
          <div className="bg-[var(--color-surface-hover)] border-l-4 border-[var(--color-accent)] p-4 rounded-lg shadow-xl flex justify-between items-center">
            <div>
              <h5 className={`text-[var(--color-accent)] font-bold uppercase tracking-wider mb-1 flex items-center gap-2 ${!marlSession ? 'text-lg' : 'text-xs'}`}>
                <Network size={!marlSession ? 20 : 14} /> {!marlSession ? 'Adaptive MARL (Multi-Agent Reinforcement Learning) Agent' : engineType === 'MARL Cooperative' ? 'Adaptive MARL (Multi-Agent Reinforcement Learning) Agent' : 'Adaptive Single-Agent RL Controller'}
              </h5>
              {marlSession && (
                <div className="flex items-center gap-3 mt-2">
                  <p className="text-base text-fuchsia-400 max-w-2xl font-bold">
                    {engineType === 'MARL Cooperative' ?
                      "High complexity detected: used MARL agent." :
                      "Low complexity detected: used RL agent."
                    }
                  </p>
                  <div className="bg-fuchsia-600 text-white border border-fuchsia-400 px-3 py-1 rounded font-black text-xs tracking-widest shadow-[0_0_10px_rgba(217,70,239,0.5)]">
                    {engineType === 'MARL Cooperative' ? 'MARL' : 'RL'}
                  </div>
                </div>
              )}
            </div>

            {!marlSession ? (
              <button
                onClick={startMARLSession}
                disabled={isStartingMARL}
                className="bg-[var(--color-accent)] hover:opacity-80 text-black px-6 py-2 rounded-lg font-bold shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isStartingMARL ? <Loader2 size={16} className="animate-spin" /> : null}
                {isStartingMARL ? "Deploying..." : "Deploy Agent"}
              </button>
            ) : (
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-xs text-[var(--color-text-muted)]">{engineType === 'MARL Cooperative' ? 'COOPERATIVE STEP' : 'RL AGENT STEP'}</div>
                  <div className="text-2xl font-mono text-[var(--color-accent)] font-bold">{marlSession.step} / 120</div>
                </div>
                <button
                  onClick={() => setIsMarlStepping(!isMarlStepping)}
                  className={`px-6 py-2 rounded-lg font-bold shadow-lg transition-all ${isMarlStepping ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/50' : 'bg-[var(--color-accent)] text-black hover:opacity-80'}`}
                >
                  {isMarlStepping ? 'PAUSE' : 'RESUME'}
                </button>
              </div>
            )}
          </div>

          {marlSession && (
            <>
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Agent Network Graph — only show for true MARL with inter-agent communication */}
                {engineType === 'MARL Cooperative' && (
                  <Card className="bg-[var(--color-surface)] flex flex-col lg:flex-[2] min-h-[400px] lg:h-[600px]">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-sm font-bold text-[var(--color-accent)] uppercase tracking-wider m-0">Agent Communication Network</h3>
                      <div className="group relative flex items-center">
                        <Info size={16} className="text-[var(--color-accent)] cursor-help" />
                        <div className="absolute top-full mt-2 left-0 w-72 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
                          Each node is an independent AI agent controlling a traffic light. Dashed lines show communication links. Green pulses = coordination signals. Red pulses = congestion warnings. Ring around each node shows queue pressure.
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 min-h-[320px]">
                      <AgentNetworkGraph agents={marlSession.agents} adjacency={marlSession.adjacency} step={marlSession.step} />
                    </div>
                  </Card>
                )}

                {/* Per-Agent Cards */}
                <div className="flex flex-col grid-cols-1 sm:grid sm:grid-cols-2 lg:flex lg:flex-col lg:flex-[1] gap-4 lg:h-[600px] lg:overflow-y-auto lg:pr-2 custom-scrollbar">
                  {marlSession.agents.map((agent, i) => (
                    <Card key={i} className="bg-[var(--color-surface)] relative overflow-hidden group shrink-0" style={{ borderTop: `4px solid ${AGENT_COLORS[i]}` }}>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: AGENT_COLORS[i] }} />
                        <div className="text-xs text-[var(--color-text-muted)] truncate font-bold">A{i + 1}: {agent.junction}</div>
                      </div>
                      <div className="flex justify-between items-end mb-3">
                        <div>
                          <div className="text-3xl font-mono font-bold text-[var(--color-text-main)]">{Math.round(agent.new_green_sec)}s</div>
                          <div className="text-xs text-[var(--color-text-muted)]">Green Time</div>
                        </div>
                        <div className={`text-sm font-bold font-mono px-2 py-1 rounded ${agent.adjustment_sec > 0 ? 'bg-green-500/20 text-green-400' : agent.adjustment_sec < 0 ? 'bg-red-500/20 text-red-400' : 'bg-[var(--color-base)] text-[var(--color-text-muted)]'}`}>
                          {agent.adjustment_sec > 0 ? '+' : ''}{agent.adjustment_sec}s
                        </div>
                      </div>

                      {/* Queue */}
                      <div className="border-t border-[var(--color-border)] pt-2 mb-2">
                        <div className="flex justify-between text-[10px] uppercase text-[var(--color-text-muted)] mb-1">
                          <span>Queue</span>
                          <span>{Math.round(agent.queue)} veh</span>
                        </div>
                        <div className="h-1.5 w-full bg-[var(--color-base)] rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-1000 ${agent.queue > 400 ? 'bg-red-500' : agent.queue > 200 ? 'bg-yellow-500' : 'bg-green-500'}`}
                            style={{ width: `${Math.min(100, (agent.queue / 600) * 100)}%` }}
                          />
                        </div>
                      </div>

                      {/* Local Reward */}
                      <div className="flex justify-between text-[10px] text-[var(--color-text-muted)]">
                        <span>Reward</span>
                        <span className={`font-mono font-bold ${agent.local_reward > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {agent.local_reward?.toFixed(2)}
                        </span>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-[var(--color-surface)] h-[300px] flex flex-col overflow-visible">
                  <h3 className="text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Per-Agent Queue Over Time</h3>
                  <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
                      <LineChart data={marlMetrics.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                        <XAxis dataKey="step" stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                        <YAxis stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                        <RechartsTooltip
                          contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                          itemStyle={{ color: 'var(--color-text-main)' }}
                          labelStyle={{ color: 'var(--color-text-muted)' }}
                        />
                        {[0, 1, 2, 3, 4].map(idx => (
                          <Line key={idx} type="monotone" dataKey={`q${idx}`} name={`Agent ${idx + 1}`} stroke={AGENT_COLORS[idx]} strokeWidth={2} dot={false} isAnimationActive={false} />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                <Card className="bg-[var(--color-surface)] h-[300px] flex flex-col overflow-visible">
                  <h3 className="text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Crowd Evacuation &amp; Global Reward</h3>
                  <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
                      <LineChart data={marlMetrics.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                        <XAxis dataKey="step" stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                        <YAxis stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                        <RechartsTooltip
                          contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                          itemStyle={{ color: 'var(--color-text-main)' }}
                          labelStyle={{ color: 'var(--color-text-muted)' }}
                        />
                        <Line type="monotone" dataKey="crowd" name="Crowd %" stroke="var(--color-accent)" strokeWidth={3} dot={false} isAnimationActive={false} />
                        <Line type="monotone" dataKey="total_reward" name="Global Reward" stroke="#00c853" strokeWidth={2} dot={false} isAnimationActive={false} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
