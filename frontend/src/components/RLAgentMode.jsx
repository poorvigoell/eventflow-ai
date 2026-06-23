import { Card } from './ui/components';
import { Activity, Zap, Loader2, Info } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts';

/**
 * RLAgentMode — Dedicated UI for Single-Agent RL signal control.
 * Rendered inside SignalsTab when the backend selects engine "Single RL".
 * Receives data from the unified /api/ai/ endpoints, mapped to RL format.
 */
export function RLAgentMode({ session, metrics, isStepping, isStarting, onStart, onToggleStepping }) {
  // Map unified agent data → simpler junction format
  const junctions = session?.agents?.map(a => ({
    name: a.junction,
    green_sec: a.new_green_sec,
    queue: a.queue,
    adjustment: a.adjustment_sec
  })) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-[var(--color-surface-hover)] border-l-4 border-[var(--color-accent)] p-4 rounded-lg shadow-xl flex justify-between items-center">
        <div>
          <h5 className={`text-[var(--color-accent)] font-bold uppercase tracking-wider mb-1 flex items-center gap-2 ${!session ? 'text-lg' : 'text-xs'}`}>
            <Activity size={!session ? 20 : 14}/> Live RL Operator
          </h5>
          {session && (
            <div className="flex items-center gap-3 mt-2">
              <p className="text-base text-fuchsia-400 max-w-2xl font-bold">
                Low complexity detected: used RL agent.
              </p>
              <div className="bg-fuchsia-600 text-white border border-fuchsia-400 px-3 py-1 rounded font-black text-xs tracking-widest shadow-[0_0_10px_rgba(217,70,239,0.5)]">
                RL
              </div>
            </div>
          )}
        </div>
        
        {!session ? (
          <button 
            onClick={onStart}
            disabled={isStarting}
            className="bg-[var(--color-accent)] hover:opacity-80 text-black px-6 py-2 rounded-lg font-bold shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStarting ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16}/>}
            {isStarting ? "Initializing..." : "Initialize Agent"}
          </button>
        ) : (
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-xs text-[var(--color-text-muted)]">SIMULATED STEP</div>
              <div className="text-2xl font-mono text-[var(--color-accent)] font-bold">{session.step} / 120</div>
            </div>
            <button 
              onClick={onToggleStepping}
              className={`px-6 py-2 rounded-lg font-bold shadow-lg transition-all ${isStepping ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/50' : 'bg-[var(--color-accent)] text-black hover:opacity-80'}`}
            >
              {isStepping ? 'PAUSE' : 'RESUME'}
            </button>
          </div>
        )}
      </div>
      
      {session && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {junctions.map((j, i) => (
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
            <Card className="bg-[var(--color-surface)] h-[300px] flex flex-col overflow-visible">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider m-0">Average Queue Length Over Time</h3>
                <div className="group relative flex items-center">
                  <div className="flex items-center justify-center transition duration-200 hover:scale-110">
                    <Info size={16} className="text-[var(--color-accent)] cursor-help" />
                  </div>
                  <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-64 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
                    <span><strong>Formula:</strong> Q<sub>t+1</sub> = max(0, Q<sub>t</sub> + A - D × g)</span><br/><br/>
                    This chart tracks the average number of vehicles stuck at red lights. The agent computes queue volume (Q) over time by adding Arrivals (A) and subtracting Discharge (D) during green time (g).
                  </div>
                </div>
              </div>
              <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                  <LineChart data={metrics.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
            
            <Card className="bg-[var(--color-surface)] h-[300px] flex flex-col overflow-visible">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider m-0">Crowd Evacuation Progress</h3>
                <div className="group relative flex items-center">
                  <div className="flex items-center justify-center transition duration-200 hover:scale-110">
                    <Info size={16} className="text-[var(--color-accent)] cursor-help" />
                  </div>
                  <div className="absolute top-full mt-2 right-0 w-64 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] font-normal z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none normal-case tracking-normal">
                    <span><strong>Formula:</strong> E<sub>t+1</sub> = max(0, E<sub>t</sub> - (V<sub>cleared</sub> / C<sub>total</sub>) × 100)</span><br/><br/>
                    Tracks the percentage of event attendees (E) still attempting to leave. Reduced at each step by the volume of vehicles successfully cleared (V) relative to the total crowd size (C).
                  </div>
                </div>
              </div>
              <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metrics.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
  );
}
