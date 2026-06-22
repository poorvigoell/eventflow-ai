import React, { useState } from 'react';
import { FileSearch, CheckCircle2, ShieldAlert, GitCommit, Clock, AlertTriangle } from 'lucide-react';
import { Card } from './ui/components';

export function AutopsyTab() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);

  const [resolvedEvents, setResolvedEvents] = useState([]);

  React.useEffect(() => {
    const fetchResolvedEvents = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/traffic/anomalies');
        const data = await response.json();
        const resolved = data.filter(a => a.status === 'resolved').map(a => ({
          id: a.id,
          name: `${a.accident_reported ? 'Accident' : a.emergency_vehicle_stuck ? 'Emergency' : 'Severe Gridlock'} - ${a.junction}`,
          priority: a.severity_level.charAt(0) + a.severity_level.slice(1).toLowerCase(),
          cause: a.accident_reported ? 'accident' : 'vehicle_breakdown',
          start_datetime: a.timestamp,
          tactics: "Algorithmic tactical plan deployed via RL agent",
          latitude: a.latitude || 12.9716,
          longitude: a.longitude || 77.5946
        }));
        setResolvedEvents(resolved);
      } catch (err) {
        console.error("Failed to fetch resolved anomalies", err);
      }
    };
    
    fetchResolvedEvents();
    // Refresh every 10 seconds
    const interval = setInterval(fetchResolvedEvents, 10000);
    return () => clearInterval(interval);
  }, []);

  const mockResolvedEvents = [
    {
      id: "EVT-801",
      name: "Vehicle Breakdown - Outer Ring Road",
      priority: "High",
      cause: "vehicle_breakdown",
      start_datetime: "2024-03-07T17:01:00Z",
      tactics: "Deployed 5 Barricades, Diverted via Sector 3",
      latitude: 12.9716,
      longitude: 77.5946
    },
    {
      id: "EVT-802",
      name: "Waterlogging - MG Road",
      priority: "Medium",
      cause: "weather_event",
      start_datetime: "2024-06-12T08:30:00Z",
      tactics: "Deployed 2 Barricades",
      latitude: 12.9716,
      longitude: 77.5946
    }
  ];

  const displayEvents = resolvedEvents.length > 0 ? resolvedEvents : mockResolvedEvents;

  const runAutopsy = async (event) => {
    setSelectedEvent(event);
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch('http://localhost:8000/api/causal-autopsy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          priority: event.priority,
          event_cause: event.cause,
          start_datetime: event.start_datetime,
          barricades_deployed: 1,
          latitude: event.latitude,
          longitude: event.longitude
        })
      });
      const data = await response.json();
      setResult(data);
    } catch (e) {
      console.error(e);
      setResult({ status: 'error', message: 'Failed to connect to Causal Engine' });
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <FileSearch className="text-[#00d2ff]" size={28} /> Post-Event Causal Autopsy
        </h2>
        <div className="text-xs bg-[var(--color-surface)] px-3 py-1.5 rounded-full border border-[var(--color-border)] text-[var(--color-text-muted)] flex items-center gap-2">
          <GitCommit size={14} className="text-[var(--color-accent)]" /> Causal Meta-Learner Active
        </div>
      </div>

      <p className="text-[var(--color-text-muted)] text-sm mb-6">
        Correlation does not equal causation. The Causal Autopsy engine uses Do-Calculus (via Microsoft EconML) to determine the <strong>Individual Treatment Effect (ITE)</strong> of historical tactical deployments, isolating exactly how many minutes your interventions saved or cost the city.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Event Selection */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Recently Resolved Events</h3>
          
          {displayEvents.map(evt => (
            <Card key={evt.id} className="transition-all duration-200 hover:border-[var(--color-accent)] group">
              <div className="flex justify-between items-start mb-2">
                <span className="font-bold text-[var(--color-text-main)] group-hover:text-[var(--color-accent)] transition-colors">{evt.name}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${evt.priority === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  {evt.priority}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mb-3">
                <Clock size={12} /> {new Date(evt.start_datetime).toLocaleString()}
              </div>
              <div className="bg-[var(--color-background)] p-2 rounded text-xs border border-white/5 font-mono text-[var(--color-text-muted)]">
                {evt.tactics}
              </div>
              <button 
                onClick={() => runAutopsy(evt)}
                className="mt-3 w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] text-xs py-1.5 rounded text-[var(--color-text-main)] font-semibold hover:bg-[var(--color-accent)] hover:text-black hover:border-[var(--color-accent)] transition-all cursor-pointer">
                Run Causal Autopsy
              </button>
            </Card>
          ))}
        </div>

        {/* Right Column: Autopsy Results */}
        <div>
          <h3 className="text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-4">Causal Inference Engine</h3>
          
          {loading ? (
            <Card className="h-48 flex flex-col items-center justify-center border-dashed border-[var(--color-border)] bg-transparent">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--color-accent)] mb-4"></div>
              <p className="text-sm text-[var(--color-text-muted)] animate-pulse">Running Causal Meta-Learner...</p>
              <p className="text-xs text-[var(--color-text-muted)]/50 mt-2">Computing Individual Treatment Effect (ITE)</p>
            </Card>
          ) : result && result.status === 'success' ? (
            <Card className={`h-auto border ${result.causal_effect_minutes < 0 ? 'border-green-500/30' : 'border-red-500/30'}`}>
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-full ${result.causal_effect_minutes < 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                  {result.causal_effect_minutes < 0 ? <CheckCircle2 size={32} /> : <AlertTriangle size={32} />}
                </div>
                <div>
                  <h4 className="text-lg font-bold text-[var(--color-text-main)] mb-1">
                    {result.causal_effect_minutes < 0 ? 'Successful Intervention' : 'Harmful Intervention'}
                  </h4>
                  <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
                    {result.message}
                  </p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)]">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">Causal Effect (ITE)</span>
                  <span className={`font-mono font-bold ${result.causal_effect_minutes < 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {result.causal_effect_minutes} minutes
                  </span>
                </div>
                <div className="w-full bg-[var(--color-surface)] h-2 rounded-full overflow-hidden flex">
                  <div className={`h-full ${result.causal_effect_minutes < 0 ? 'bg-green-400' : 'bg-red-400'}`} style={{ width: '100%' }}></div>
                </div>
                <p className="text-[10px] text-[var(--color-text-muted)] mt-3 italic">
                  *This metric isolates the exact time saved/lost exclusively due to the deployment of barricades, controlling for confounding variables like weather, event priority, and time of day.
                </p>
              </div>
            </Card>
          ) : result && result.status === 'error' ? (
            <Card className="border-red-500/30 bg-red-500/5">
              <div className="flex items-center gap-3 text-red-400 mb-2">
                <ShieldAlert size={20} />
                <span className="font-bold">Autopsy Failed</span>
              </div>
              <p className="text-sm text-red-400/80">{result.message}</p>
            </Card>
          ) : (
            <Card className="h-48 flex flex-col items-center justify-center border-dashed border-[var(--color-border)] bg-transparent">
              <FileSearch size={32} className="text-[var(--color-text-muted)]/30 mb-3" />
              <p className="text-sm text-[var(--color-text-muted)]">Select an event to run Causal Autopsy</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
