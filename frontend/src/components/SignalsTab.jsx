import React, { useState, useEffect, useRef } from 'react';
import { Card } from './ui/components';
import { Radio, Brain, Activity, Zap, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

export const SignalsTab = ({ signals, eventConfig }) => {
  const [isRLMode, setIsRLMode] = useState(false);
  const [rlStatus, setRlStatus] = useState({ model_exists: false });
  const [rlSession, setRlSession] = useState(null);
  const [rlMetrics, setRlMetrics] = useState({ history: [] });
  const [isStepping, setIsStepping] = useState(false);
  const [isStartingRL, setIsStartingRL] = useState(false);
  
  const timerRef = useRef(null);

  useEffect(() => {
    // Check if RL model is available
    fetch('http://localhost:8000/api/rl/status')
      .then(res => res.json())
      .then(data => {
        if (data.model_exists) setRlStatus(data);
      })
      .catch(err => console.error("RL Status error:", err));
      
    return () => {
      stopAutoStep();
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
  
  const stopAutoStep = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setIsStepping(false);
  };

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
          <Radio className="text-[var(--color-accent)]" size={28}/> Adaptive Signal Control
        </h2>
        
        {rlStatus.model_exists && (
          <div className="flex bg-[var(--color-surface)] rounded-lg p-1 border border-[var(--color-border)]">
            <button 
              onClick={() => setIsRLMode(false)}
              className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${!isRLMode ? 'bg-[var(--color-surface-hover)] text-[var(--color-text-main)] shadow-md' : 'text-[var(--color-text-muted)]'}`}
            >
              Webster Baseline
            </button>
            <button 
              onClick={() => setIsRLMode(true)}
              className={`px-4 py-2 rounded-md text-sm font-bold flex items-center gap-2 transition-all ${isRLMode ? 'bg-[var(--color-accent)] text-black shadow-md' : 'text-[var(--color-text-muted)]'}`}
            >
              <Brain size={16} /> RL Agent
            </button>
          </div>
        )}
      </div>
      
      {!isRLMode ? (
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
                  <h3 className="text-sm font-bold text-[var(--color-text-muted)] mb-4 uppercase tracking-wider">Green Split Optimization</h3>
                  <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                        <XAxis type="number" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
                        <YAxis dataKey="name" type="category" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} width={100} />
                        <RechartsTooltip 
                          cursor={false}
                          contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                          itemStyle={{ color: 'var(--color-text-main)' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '12px' }}/>
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
      ) : (
        // --- RL AGENT MODE ---
        <div className="space-y-6 animate-fade-in">
          <div className="bg-[var(--color-surface-hover)] border-l-4 border-[var(--color-accent)] p-4 rounded-lg shadow-xl flex justify-between items-center">
            <div>
              <h5 className="text-[var(--color-accent)] font-bold uppercase tracking-wider text-xs mb-1 flex items-center gap-2">
                <Activity size={14}/> Live RL Operator
              </h5>
              <p className="text-sm text-[var(--color-text-main)]">The RL Agent is actively monitoring simulated queues and adjusting green splits in real-time.</p>
            </div>
            
            {!rlSession ? (
              <button 
                onClick={startRLSession}
                disabled={isStartingRL}
                className="bg-[var(--color-accent)] hover:opacity-80 text-black px-6 py-2 rounded-lg font-bold shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isStartingRL ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16}/>}
                {isStartingRL ? "Initializing..." : "Initialize Agent"}
              </button>
            ) : (
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-xs text-[var(--color-text-muted)]">SIMULATED STEP</div>
                  <div className="text-2xl font-mono text-[var(--color-accent)] font-bold">{rlSession.step} / 120</div>
                </div>
                <button 
                  onClick={() => setIsStepping(!isStepping)}
                  className={`px-6 py-2 rounded-lg font-bold shadow-lg transition-all ${isStepping ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/50' : 'bg-[var(--color-accent)] text-black hover:opacity-80'}`}
                >
                  {isStepping ? 'PAUSE' : 'RESUME'}
                </button>
              </div>
            )}
          </div>
          
          {rlSession && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {rlSession.junctions.map((j, i) => (
                  <Card key={i} className="bg-[var(--color-surface)] border-t-4 border-t-[var(--color-accent)] relative overflow-hidden group">
                    <div className="text-xs text-[var(--color-text-muted)] truncate mb-2">{j.name}</div>
                    <div className="flex justify-between items-end mb-4">
                      <div>
                        <div className="text-3xl font-mono font-bold text-[var(--color-text-main)]">{Math.round(j.green_sec)}s</div>
                        <div className="text-xs text-[var(--color-text-muted)]">Main Green</div>
                      </div>
                      <div className={`text-sm font-bold font-mono px-2 py-1 rounded ${j.adjustment > 0 ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)]' : j.adjustment < 0 ? 'bg-red-500/20 text-red-400' : 'bg-[var(--color-base)] text-[var(--color-text-muted)]'}`}>
                        {j.adjustment > 0 ? '+' : ''}{j.adjustment}s
                      </div>
                    </div>
                    
                    <div className="mt-4 border-t border-[var(--color-border)] pt-2">
                      <div className="flex justify-between text-[10px] uppercase text-[var(--color-text-muted)] mb-1">
                        <span>Queue</span>
                        <span>{Math.round(j.queue)} veh</span>
                      </div>
                      <div className="h-1.5 w-full bg-[var(--color-base)] rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-1000 ${j.queue > 400 ? 'bg-red-500' : j.queue > 200 ? 'bg-yellow-500' : 'bg-[var(--color-accent)]'}`}
                          style={{ width: `${Math.min(100, (j.queue / 600) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-[var(--color-surface)] h-[300px] flex flex-col">
                  <h3 className="text-sm font-bold text-[var(--color-text-muted)] mb-2 uppercase tracking-wider">Average Queue Length Over Time</h3>
                  <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={rlMetrics.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                        <XAxis dataKey="step" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
                        <YAxis stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
                        <RechartsTooltip 
                          contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                          itemStyle={{ color: 'var(--color-text-main)' }}
                          labelStyle={{ color: 'var(--color-text-muted)' }}
                        />
                        <Line type="monotone" dataKey="avg_queue" stroke="#ef4444" strokeWidth={3} dot={false} isAnimationActive={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
                
                <Card className="bg-[var(--color-surface)] h-[300px] flex flex-col">
                  <h3 className="text-sm font-bold text-[var(--color-text-muted)] mb-2 uppercase tracking-wider">Crowd Evacuation Progress</h3>
                  <div className="flex-1 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={rlMetrics.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                        <XAxis dataKey="step" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} />
                        <YAxis stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-muted)', fontSize: 10}} domain={[0, 100]} />
                        <RechartsTooltip 
                          contentStyle={{ backgroundColor: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}
                          itemStyle={{ color: 'var(--color-text-main)' }}
                          labelStyle={{ color: 'var(--color-text-muted)' }}
                        />
                        <Line type="monotone" dataKey="crowd" stroke="var(--color-accent)" strokeWidth={3} dot={false} isAnimationActive={false} />
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
