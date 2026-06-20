import React, { useState } from 'react';
import { Card } from './ui/components';
import { AlertTriangle, Info, Bell, MapPin, Zap, RefreshCw, CarFront, Clock, CheckCircle2, ShieldAlert, Flame, Ambulance } from 'lucide-react';
import axios from 'axios';

export const AlertsTab = ({ anomalies, setAnomalies }) => {
  const [loading, setLoading] = useState(false);

  const injectChaos = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/traffic/inject-anomaly', {});
      // We do not call setAnomalies here because the backend broadcasts 
      // the new anomaly via WebSocket, which App.jsx listens to and adds to state.
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const clearAnomaly = async (id) => {
    try {
      await axios.post(`http://localhost:8000/api/traffic/clear-anomaly/${id}`);
      setAnomalies(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved', resolved_at: new Date().toISOString() } : a));
    } catch (e) {
      console.error(e);
    }
  };

  const activeAnomalies = anomalies.filter(a => a.status !== 'resolved').sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0));
  const pastAnomalies = anomalies.filter(a => a.status === 'resolved').sort((a, b) => new Date(b.resolved_at || 0) - new Date(a.resolved_at || 0)).slice(0, 5);

  const renderAnomalyCard = (anomaly, isActive) => {
    let accentColor = 'var(--color-accent)';
    if (anomaly.severity_level === 'CRITICAL') accentColor = '#15803d'; // Dark Green
    else if (anomaly.severity_level === 'HIGH') accentColor = '#22c55e'; // Med Green
    else if (anomaly.severity_level === 'MODERATE') accentColor = '#86efac'; // Light Green
    if (!isActive) accentColor = 'var(--color-text-muted)';

    // Ensure text is readable on the background pill
    const textColor = anomaly.severity_level === 'MODERATE' ? '#064e3b' : '#ffffff';

    return (
      <Card key={`${anomaly.id}-${anomaly.timestamp}`} className={`border-l-4 overflow-hidden relative ${isActive ? '' : 'opacity-70 bg-[var(--color-base)]'}`} style={{ borderLeftColor: accentColor }}>
        {isActive && (
          <div className="absolute top-0 right-0 p-4">
            <button
              onClick={() => clearAnomaly(anomaly.id)}
              className="text-xs font-bold text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] bg-[var(--color-surface-hover)] border border-[var(--color-border)] px-3 py-1 rounded-full transition-colors"
            >
              Resolve
            </button>
          </div>
        )}

        <div className="flex items-start gap-4 pr-24">
          <div className="p-3 rounded-xl flex-shrink-0" style={{ backgroundColor: `${accentColor}20` }}>
            <MapPin size={24} style={{ color: accentColor }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-bold px-2 py-0.5 rounded uppercase tracking-wider" style={{ backgroundColor: accentColor, color: textColor }}>
                {anomaly.severity_level || 'SEVERE'} GRIDLOCK
              </span>
              <span className="text-xs text-[var(--color-text-muted)] whitespace-nowrap">
                {isActive ? new Date(anomaly.timestamp).toLocaleTimeString() : `Resolved at ${new Date(anomaly.resolved_at).toLocaleTimeString()}`}
              </span>
              {anomaly.emergency_vehicle_stuck && isActive && (
                <span className="text-xs font-bold bg-[#15803d]/20 text-[#22c55e] border border-[#22c55e]/50 px-2 py-0.5 rounded uppercase flex items-center gap-1 animate-pulse">
                  🚨 Emergency Vehicle Stuck
                </span>
              )}
              {anomaly.accident_reported && isActive && (
                <span className="text-xs font-bold bg-[#15803d]/20 text-[#22c55e] border border-[#22c55e]/50 px-2 py-0.5 rounded uppercase">
                  ⚠️ Accident Reported
                </span>
              )}
            </div>

            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-[var(--color-text-main)]">{anomaly.junction}</h3>
              {anomaly.severity_score && (
                <div className="text-right">
                  <div className="text-2xl font-black" style={{ color: accentColor }}>{anomaly.severity_score}<span className="text-sm font-normal text-[var(--color-text-muted)]">/100</span></div>
                  <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Severity Score</div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
              <div className="lg:col-span-2 flex flex-col gap-3 justify-between">
                <div className="bg-[var(--color-base)] px-4 py-3 rounded-lg border border-[var(--color-border)] flex items-center justify-between flex-1">
                  <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider whitespace-nowrap">Current Speed</span>
                  <span className="font-black text-[var(--color-text-main)] text-lg whitespace-nowrap">{anomaly.current_speed_kmh} <span className="text-xs font-normal text-[var(--color-text-muted)]">/ 40 km/h</span></span>
                </div>
                <div className="bg-[var(--color-base)] px-4 py-3 rounded-lg border border-[var(--color-border)] flex items-center justify-between flex-1">
                  <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider whitespace-nowrap">Jam Factor</span>
                  <span className="font-black text-lg whitespace-nowrap" style={{ color: accentColor }}>{anomaly.jam_factor} <span className="text-xs font-normal text-[var(--color-text-muted)]">/ 10</span></span>
                </div>
              </div>
              <div className="bg-[var(--color-base)] p-3 rounded-lg border border-[var(--color-border)] flex flex-col justify-between">
                <p className="text-xs text-[var(--color-text-muted)] mb-2">Emergency ETAs</p>
                <div className="space-y-1.5 flex-1 flex flex-col justify-end">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-1 text-[var(--color-text-muted)]"><CarFront size={14} /> Police</span>
                    <span className="font-bold" style={{ color: accentColor }}>{anomaly.emergency_etas?.police || anomaly.emergency_eta_mins}m</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-1 text-[var(--color-text-muted)]"><Flame size={14} /> Fire</span>
                    <span className="font-bold text-orange-500">{anomaly.emergency_etas?.fire_truck || anomaly.emergency_eta_mins}m</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-1 text-[var(--color-text-muted)]"><Ambulance size={14} /> Med</span>
                    <span className="font-bold text-red-500">{anomaly.emergency_etas?.ambulance || anomaly.emergency_eta_mins}m</span>
                  </div>
                </div>
              </div>
              <div className="bg-[var(--color-base)] p-3 rounded-lg border border-[var(--color-border)] flex flex-col justify-between">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Contact Center</p>
                <div>
                  <div className="flex items-start gap-2 font-bold text-sm text-[var(--color-text-main)]" title={anomaly.traffic_control_center || 'Local Police Station'}>
                    <ShieldAlert size={16} className="shrink-0 mt-0.5" style={{ color: accentColor }} />
                    <span className="leading-tight">{anomaly.traffic_control_center || 'Local Police Station'}</span>
                  </div>
                  {anomaly.traffic_control_center_dist_km > 0 && (
                    <p className="text-[10px] text-[var(--color-text-muted)] mt-1 ml-6 uppercase tracking-wider">
                      {anomaly.traffic_control_center_dist_km} km away
                    </p>
                  )}
                </div>
              </div>
            </div>

            {isActive && anomaly.tactical_plan && (
              <div className="bg-[var(--color-base)] p-4 rounded-xl border border-[var(--color-border)]">
                <h4 className="text-sm font-bold text-[var(--color-text-main)] mb-3 flex items-center gap-2">
                  <Zap size={16} style={{ color: accentColor }} />
                  Algorithmic Tactical Plan Generated
                </h4>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: accentColor }} />
                    {anomaly.tactical_plan.police_dispatch}
                  </li>
                  <li className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: accentColor }} />
                    {anomaly.tactical_plan.diversion}
                  </li>
                  <li className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: accentColor }} />
                    {anomaly.tactical_plan.signals}
                  </li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-[var(--color-text-main)] flex items-center gap-3">
            <AlertTriangle className="text-[var(--color-accent)]" size={32} />
            Live Traffic Anomalies
          </h1>
          <p className="text-[var(--color-text-muted)] mt-1">Real-time gridlock detection and tactical response.</p>
        </div>
        <button
          onClick={injectChaos}
          disabled={loading}
          className="bg-[var(--color-accent)]/10 hover:bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]/30 px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all disabled:opacity-50"
        >
          {loading ? <RefreshCw className="animate-spin" size={20} /> : <Zap size={20} />}
          Inject Chaos (Simulate)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-8">

          {/* Active Anomalies Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-[var(--color-text-main)] flex items-center gap-2 border-b border-[var(--color-border)] pb-2">
              <Zap size={20} className="text-[var(--color-accent)]" /> Active Traffic Anomalies
            </h2>
            {activeAnomalies.length === 0 ? (
              <Card className="flex flex-col items-center justify-center h-48 text-center border-dashed border-2 border-[var(--color-border)] bg-transparent">
                <CheckCircle2 size={48} className="text-[var(--color-accent)]/50 mb-4" />
                <h3 className="text-xl font-bold text-[var(--color-text-main)] mb-2">No Active Anomalies</h3>
                <p className="text-[var(--color-text-muted)] max-w-md">The city traffic network is currently flowing normally.</p>
              </Card>
            ) : (
              activeAnomalies.map(anomaly => renderAnomalyCard(anomaly, true))
            )}
          </div>

          {/* Past Anomalies Section */}
          {pastAnomalies.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-[var(--color-text-muted)] flex items-center gap-2 border-b border-[var(--color-border)] pb-2">
                <Clock size={20} /> Resolved Anomalies (Recent)
              </h2>
              {pastAnomalies.map(anomaly => renderAnomalyCard(anomaly, false))}
            </div>
          )}

        </div>

        {/* Right Column: Info Tooltip */}
        <div className="space-y-4">
          <Card className="bg-[var(--color-accent)]/5 border-[var(--color-accent)]/20 sticky top-4">
            <div className="flex items-center gap-3 mb-4">
              <h3 className="font-bold text-[var(--color-accent)]">How It Works</h3>
            </div>

            <div className="space-y-4 text-xs text-[var(--color-text-muted)] leading-relaxed">
              <p className="text-sm mb-2">
                EventFlow is a smart traffic assistant that automatically spots traffic jams and helps fix them in real-time.
              </p>

              <div className="border-t border-[var(--color-border)] pt-3">
                <p className="text-[var(--color-accent)] font-semibold mb-2">THE PIPELINE:</p>
                <ul className="list-disc pl-4 space-y-3">
                  <li><strong>Live Tracking:</strong> The system constantly scans the live TomTom traffic map to detect severe delays and accidents as they happen in the city.</li>
                  <li><strong>Smart Estimates:</strong> Once a jam is found, the system calculates exactly how long it will take police and ambulances to arrive, taking the current traffic speeds into account.</li>
                  <li><strong>Instant Solutions:</strong> It automatically generates an action plan. It figures out exactly how long to keep traffic lights green to clear the jam, and finds the fastest parallel streets to divert incoming cars.</li>
                  <li><strong>Demo Mode:</strong> Click the "Simulate Chaos" button to fake a massive traffic jam. This lets you see exactly how the system reacts without having to wait for a real car crash to happen!</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
