import React, { useState, useEffect } from 'react';
import { Card } from './ui/components';
import { AlertTriangle, Info, Bell, MapPin, Zap, RefreshCw, CarFront, Clock, CheckCircle2, ShieldAlert, Flame, Ambulance, Activity, Loader2 } from 'lucide-react';
import axios from 'axios';
import MapOverlay from './MapOverlay';
import { TimelineChart } from './TimelineChart';

const LIVE_CACHE_KEY = 'eventflow_live_traffic_state';
const CACHE_EXPIRY_MS = 30 * 60 * 1000;

function readLiveCache() {
  try {
    const raw = localStorage.getItem(LIVE_CACHE_KEY);
    if (!raw) return null;
    const { timestamp, state } = JSON.parse(raw);
    if (Date.now() - timestamp >= CACHE_EXPIRY_MS) return null;
    // Reject cache if coordinates are invalid (NaN/null) to prevent map crashes
    const lat = state?.localLat;
    const lng = state?.localLng;
    if (typeof lat !== 'number' || isNaN(lat) || typeof lng !== 'number' || isNaN(lng)) return null;
    return state;
  } catch {}
  return null;
}

const InfoTooltip = ({ text, alignRight = false }) => (
  <div className={`absolute ${alignRight ? 'right-4' : 'left-4'} top-4 z-50`}>
    <div className="group inline-flex">
      <div className="flex items-center justify-center transition duration-200 hover:scale-110">
        <Info size={16} className="text-[var(--color-accent)] cursor-help" />
      </div>
      <div className={`absolute ${alignRight ? 'right-0' : 'left-0'} top-full mt-2 w-60 p-3.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl text-[13px] leading-5 text-[var(--color-text-main)] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200`}>
        {text}
      </div>
    </div>
  </div>
);

export const AlertsTab = ({ anomalies, setAnomalies, setGlobalData, setGlobalLat, setGlobalLng, setGlobalShowPin, setGlobalEventType, setActiveAnalysisSource, activeAnalysisSource, handleTabChange, activeTab }) => {
  const [internalLoading, setInternalLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const cachedLive = readLiveCache();
  
  // Local state — isolated from the prediction dashboard
  const [localData, setLocalData] = useState(cachedLive?.localData ?? null);
  const [localLoading, setLocalLoading] = useState(false);
  const [localLat, setLocalLat] = useState(cachedLive?.localLat ?? 12.9716);
  const [localLng, setLocalLng] = useState(cachedLive?.localLng ?? 77.5946);
  const [localShowPin, setLocalShowPin] = useState(cachedLive?.localShowPin ?? false);
  const [localLocationName, setLocalLocationName] = useState(cachedLive?.localLocationName ?? '');
  const [showEmergencyRoutes, setShowEmergencyRoutes] = useState(cachedLive?.showEmergencyRoutes ?? true);

  // Clear live traffic pin when prediction setup becomes the active source
  useEffect(() => {
    if (activeAnalysisSource === 'prediction_setup') {
      setLocalShowPin(false);
      setLocalData(null);
      setLocalLocationName('');
    }
  }, [activeAnalysisSource]);

  // Save local state to cache whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(LIVE_CACHE_KEY, JSON.stringify({
        timestamp: Date.now(),
        state: { localData, localLat, localLng, localShowPin, localLocationName, showEmergencyRoutes }
      }));
    } catch (e) {
      console.warn('Live cache write failed:', e);
    }
  }, [localData, localLat, localLng, localShowPin, localLocationName, showEmergencyRoutes]);

  const injectChaos = async () => {
    setInternalLoading(true);
    try {
      const junctions = ["Silk Board Junction", "Madiwala Checkpost", "Koramangala 80ft Road", "Indiranagar 100ft Road", "Marathahalli Bridge"];
      const randomJunction = junctions[Math.floor(Math.random() * junctions.length)];
      await axios.post('http://localhost:8000/api/traffic/inject-anomaly', {
        junction_name: randomJunction
      });
    } catch (e) {
      console.error(e);
      if (e.response && e.response.status === 429) {
        window.alert("Please wait 10 seconds before simulating another anomaly to avoid spamming the system.");
      }
    } finally {
      setInternalLoading(false);
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

  const analyzeLiveAnomaly = async (anomaly) => {
    const safeLat = parseFloat(anomaly.latitude) || 12.9716;
    const safeLng = parseFloat(anomaly.longitude) || 77.5946;

    // Immediately update global state to clear Prediction Setup map and pin
    if (setActiveAnalysisSource) setActiveAnalysisSource('alerts_tab');
    if (setGlobalShowPin) setGlobalShowPin(false);
    if (setGlobalData) setGlobalData(null);

    setLocalLoading(true);
    setLocalData(null);
    setLocalLat(safeLat);
    setLocalLng(safeLng);
    setLocalLocationName(anomaly.junction);
    setLocalShowPin(true);
    
    try {
      const response = await axios.post('http://localhost:8000/api/predict', {
        event_type: anomaly.accident_reported ? "accident" : "gridlock",
        latitude: safeLat,
        longitude: safeLng,
        zone: "Central",
        start_time: new Date().toISOString(),
        duration_hours: 2,
        weather_rain: false,
        multi_event_mode: false,
        emergency_mode: anomaly.emergency_vehicle_stuck || anomaly.accident_reported
      }, { timeout: 300000 });
      setLocalData(response.data);
      
      // Update global context so other tabs (Tactical, Signals, Dispersal) get this data
      if (setGlobalData) setGlobalData(response.data);
      // We purposefully DO NOT setGlobalShowPin(true) here because the Prediction Setup pin should stay hidden
      if (setGlobalLat) setGlobalLat(safeLat);
      if (setGlobalLng) setGlobalLng(safeLng);
      if (setGlobalEventType) setGlobalEventType(anomaly.accident_reported ? "accident" : "gridlock");

    } catch (e) {
      console.error(e);
      const errMsg = e.response ? JSON.stringify(e.response.data) : e.message;
      window.alert("Live analysis failed: " + errMsg);
    } finally {
      setLocalLoading(false);
    }
  };

  const activeAnomalies = anomalies.filter(a => a.status !== 'resolved').sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0));

  const renderAnomalyCard = (anomaly, isActive) => {
    let accentColor = 'var(--color-accent)';
    if (anomaly.severity_level === 'CRITICAL') accentColor = '#15803d';
    else if (anomaly.severity_level === 'HIGH') accentColor = '#22c55e';
    else if (anomaly.severity_level === 'MODERATE') accentColor = '#86efac';
    if (!isActive) accentColor = 'var(--color-text-muted)';

    const textColor = anomaly.severity_level === 'MODERATE' ? '#064e3b' : '#ffffff';

    return (
      <Card key={`${anomaly.id}-${anomaly.timestamp}`} className={`border-l-4 overflow-hidden p-3 ${isActive ? '' : 'opacity-70 bg-[var(--color-base)]'}`} style={{ borderLeftColor: accentColor }}>
        <div className="flex flex-col gap-2">
          
          {/* Top Row: Severity & Time & Buttons */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider" style={{ backgroundColor: accentColor, color: textColor }}>
                {anomaly.severity_level || 'SEVERE'} GRIDLOCK
              </span>
              <span className="text-[10px] text-[var(--color-text-muted)] whitespace-nowrap">
                {isActive ? new Date(anomaly.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : `Resolved`}
              </span>
            </div>
            
            {isActive && (
              <div className="flex gap-1.5 shrink-0">
                <button
                  onClick={() => analyzeLiveAnomaly(anomaly)}
                  disabled={localLoading}
                  className="text-[9px] font-bold text-[var(--color-text-main)] bg-[var(--color-accent)]/10 hover:bg-[var(--color-accent)]/20 border border-[var(--color-accent)]/30 px-2 py-1 rounded transition-colors uppercase tracking-wider disabled:opacity-50"
                >
                  Analyze
                </button>
                <button
                  onClick={() => clearAnomaly(anomaly.id)}
                  className="text-[9px] font-bold text-[var(--color-text-muted)] hover:text-[var(--color-text-main)] bg-[var(--color-surface-hover)] border border-[var(--color-border)] px-2 py-1 rounded transition-colors uppercase tracking-wider"
                >
                  Resolve
                </button>
              </div>
            )}
          </div>

          <h3 className="text-sm font-bold text-[var(--color-text-main)] leading-tight truncate">{anomaly.junction}</h3>

          {isActive && (
            <div className="grid grid-cols-2 gap-2 mt-1">
              <div className="bg-[var(--color-base)] p-1.5 rounded border border-[var(--color-border)] flex flex-col items-center justify-center">
                <span className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Speed</span>
                <span className="font-bold text-sm text-[var(--color-text-main)]">{anomaly.current_speed_kmh} <span className="text-[9px] text-[var(--color-text-muted)]">km/h</span></span>
              </div>
              <div className="bg-[var(--color-base)] p-1.5 rounded border border-[var(--color-border)] flex flex-col items-center justify-center">
                <span className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Jam Factor</span>
                <span className="font-bold text-sm" style={{ color: accentColor }}>{anomaly.jam_factor} <span className="text-[9px] text-[var(--color-text-muted)]">/ 10</span></span>
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  };

  return (
    <div className="flex flex-col w-full max-w-[1400px] mx-auto gap-6">
      
      {/* PAGE HEADER */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/20 flex items-center justify-center">
          <Activity size={20} className="text-[var(--color-accent)]" />
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[var(--color-text-main)] uppercase">Live Traffic Monitoring</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Real-time anomaly detection and predictive routing analysis.</p>
        </div>
      </div>

      {/* TOP ROW: Map & Alerts */}
      <div className="flex w-full gap-6 shrink-0 h-[500px]">
        {/* Map Container (2/3) */}
        <div className="w-2/3 h-full rounded-xl overflow-hidden shadow-2xl relative border border-[var(--color-border)] bg-[var(--color-base)] shrink-0">
          <div className="absolute top-0 left-0 right-0 z-[500] flex justify-between items-center w-full p-4 pointer-events-none">
            <h2 className="text-sm font-bold flex items-center gap-2 bg-[var(--color-surface)]/80 backdrop-blur-md px-4 py-2 rounded-xl shadow-2xl uppercase tracking-widest text-[var(--color-text-main)]">
              <MapPin className="text-[var(--color-accent)]" size={16} /> Live City Traffic Map
            </h2>
            <div className="pointer-events-auto flex items-center gap-2">
              {localData?.emergency_routes && (
                <label className="flex items-center gap-3 bg-[var(--color-surface)]/80 hover:bg-[var(--color-surface-hover)] border border-[var(--color-border)] px-4 py-2 rounded-xl cursor-pointer transition-colors shadow-2xl backdrop-blur-md group">
                  <span className="text-xs font-bold text-[var(--color-text-main)] uppercase tracking-widest">Emergency Routing</span>
                  <div className="relative inline-flex items-center">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={showEmergencyRoutes}
                      onChange={(e) => setShowEmergencyRoutes(e.target.checked)}
                    />
                    <div className="w-8 h-4 bg-[var(--color-base)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#00e676] border border-[var(--color-border)] shadow-inner"></div>
                  </div>
                </label>
              )}
              {localData ? (
                <button 
                  onClick={() => setLocalData(null)}
                  className="bg-[var(--color-base)] hover:bg-[var(--color-surface-hover)] border border-[var(--color-border)] px-4 py-2 rounded-xl shadow-2xl transition-colors text-xs font-bold uppercase tracking-widest text-[var(--color-text-main)]"
                >
                  Clear Analysis
                </button>
              ) : (
                <div className="flex items-center gap-2 bg-[var(--color-surface)]/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-[var(--color-border)] shadow-2xl">
                   <span className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></span>
                   <span className="text-xs font-bold text-white uppercase tracking-widest">TomTom Live Data</span>
                </div>
              )}
            </div>
          </div>

          <div className="w-full h-full relative pointer-events-auto">
            <MapOverlay
              lat={localData ? localLat : 12.9716}
              lng={localData ? localLng : 77.5946}
              showPin={localData ? localShowPin : false}
              isLiveTrafficMode={!localData}
              setLocation={() => {}}
              locationName={localData ? localLocationName : ""}
              setLocationName={() => {}}
              predictionData={localData ? localData.prediction : null}
              criticalRoads={localData ? localData.critical_roads : null}
              emergencyRoutes={(localData && localData.emergency_routes && showEmergencyRoutes) ? localData.emergency_routes : null}
              initialMapData={null}
              targetBoundary={null}
              setTargetBoundary={() => {}}
              isActive={activeTab === 'alerts'}
            />
          </div>
        </div>

        {/* Alerts Container (1/3) */}
        <div className="w-1/3 h-full overflow-y-auto custom-scrollbar flex flex-col shrink-0 bg-[var(--color-surface)]/50 border border-[var(--color-border)] rounded-xl shadow-2xl relative">
          <div className="flex items-center justify-between sticky top-0 bg-[#0a0a0a] z-10 px-5 py-4 border-b border-[var(--color-border)] rounded-t-xl">
            <div>
              <h1 className="text-xl font-black tracking-tight text-[var(--color-text-main)] flex items-center gap-2">
                <AlertTriangle className="text-[var(--color-accent)]" size={24} />
                Live Alerts
              </h1>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">Real-time detection and response.</p>
            </div>
            <button
              onClick={injectChaos}
              disabled={internalLoading}
              className="bg-[var(--color-accent)]/10 hover:bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]/30 p-2 rounded-lg transition-all disabled:opacity-50"
              title="Send Sample Feed"
            >
              <RefreshCw className={internalLoading ? "animate-spin" : ""} size={18} />
            </button>
          </div>

          <div className="px-5 pb-5 mt-4">
            {activeAnomalies.length === 0 ? (
              <Card className="flex flex-col items-center justify-center h-32 text-center border-dashed border-2 border-[var(--color-border)] bg-transparent">
                <CheckCircle2 size={32} className="text-[var(--color-accent)]/50 mb-2" />
                <p className="text-xs text-[var(--color-text-muted)] max-w-[200px]">The city traffic network is flowing normally.</p>
              </Card>
            ) : (
              <div className="flex flex-col gap-3 pb-4">
                {activeAnomalies.map(anomaly => renderAnomalyCard(anomaly, true))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* BOTTOM ROW: Analysis Container (Full width) */}
      {localLoading ? (
          <div className="h-[250px] w-full shrink-0 bg-[var(--color-surface)] rounded-xl shadow-2xl flex flex-col items-center justify-center text-[var(--color-accent)]">
            <Loader2 size={40} className="animate-spin mb-4" />
            <h2 className="text-lg font-bold text-[var(--color-text-main)]">Simulating Dispatch Patterns...</h2>
            <p className="text-sm text-[var(--color-text-muted)] mt-1">Calculating risk probabilities and timeline.</p>
          </div>
      ) : (localData && localData.prediction) && (
          <div className="w-full flex flex-col gap-6 animate-fade-in shrink-0">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Timeline Chart */}
              <div className="lg:col-span-1 h-full bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] p-5 rounded-xl shadow-2xl flex flex-col min-w-0 relative overflow-hidden group">
                <TimelineChart timelineData={localData.timeline} />
              </div>

              {/* Metrics Grid */}
              <div className="lg:col-span-1 grid grid-cols-2 gap-4 min-w-0">
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-accent)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Calculated using a RandomForest ML Model trained on historical city traffic data, predicting the excess traffic volume based on event type, weather, and time of day." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 z-10">Surge</span>
                  <span className="text-4xl font-bold text-[var(--color-accent)] z-10">+{localData.prediction.total_incidents}</span>
                </div>
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-accent)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Derived from the ML model's confidence rating combined with a cascading failure graph analysis of surrounding road network bottlenecks." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 z-10">Risk Score</span>
                  <span className="text-4xl font-bold text-[var(--color-accent)] z-10">{Math.round(localData.prediction.confidence * 100)}</span>
                </div>
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-text-main)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Calculated dynamically using a queuing theory allocation algorithm factoring in predicted incidents and available city resources." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-accent)] uppercase tracking-widest mb-1 z-10">Dispatch Units</span>
                  <span className="text-4xl font-bold text-[var(--color-text-main)] z-10">{localData.dispatch.total_units}</span>
                </div>
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-text-main)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Economic impact modeling of lost person-hours due to gridlock, converted to local currency including congestion surcharges." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-accent)] uppercase tracking-widest mb-1 z-10">Est. Cost</span>
                  <span className="text-4xl font-bold text-[var(--color-text-main)] z-10">₹{localData.economic_impact.cost_lakhs}L</span>
                </div>
              </div>

              {/* Alerts & Econ */}
              <div className="lg:col-span-1 flex flex-col gap-4 min-w-[280px]">
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center relative shadow-2xl group">
                  <div className="absolute right-0 top-0 w-24 h-24 bg-[var(--color-text-muted)]/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2" />
                  <h2 className={`text-[11px] font-bold mb-2 flex items-center gap-2 uppercase tracking-widest ${localData.dispatch.alert_level === 'RED' ? 'text-red-500' :
                      localData.dispatch.alert_level === 'AMBER' ? 'text-amber-500' :
                        'text-[var(--color-accent)]'
                    }`}>
                    <AlertTriangle size={16} /> {localData.dispatch.alert_level}
                  </h2>
                  <p className="text-sm text-[var(--color-text-muted)] leading-relaxed font-medium">{localData.dispatch.justification}</p>
                </div>

                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-start relative shadow-2xl group">
                  <InfoTooltip text="Suggested emergency services are chosen from nearby high-risk junctions and predicted incident demand." alignRight />
                  <div className="absolute right-0 top-0 w-24 h-24 bg-[var(--color-accent)]/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2" />
                  <h2 className="text-[11px] font-bold mb-3 flex items-center gap-2 text-[var(--color-accent)] uppercase tracking-widest">
                    <AlertTriangle size={16} /> Emergency Services
                  </h2>
                  <div className="flex flex-col gap-3">
                    {localData.emergency_services?.map((svc, idx) => (
                      <div key={idx} className="flex justify-between items-center text-sm border-b border-[var(--color-border)] pb-2 last:border-0">
                        <span className="text-[var(--color-text-main)] font-medium flex items-center gap-2">
                          {svc.type === 'hospital' ? '🏥' : svc.type === 'fire' ? '🚒' : '🚓'} {svc.name}
                        </span>
                        <span className="font-bold text-[var(--color-accent)]">{svc.distance_km} km</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Full Width Economic Impact Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center items-center shadow-2xl relative group">
                <InfoTooltip text="Estimated from predicted incident volume and average delay per vehicle during congestion." />
                <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 relative z-10">Person-Hours Lost</span>
                <span className="font-bold text-[var(--color-accent)] text-3xl relative z-10 mb-2">{localData.economic_impact.person_hours} hrs</span>
                <span className="text-sm text-[var(--color-text-muted)] text-center leading-relaxed max-w-[90%]">Total civic productivity delay estimated based on localized gridlock volume.</span>
              </div>

              <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center items-center shadow-2xl relative group">
                <InfoTooltip text="Derived from predicted incident counts and assumed average people per vehicle in the impacted network." />
                <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 relative z-10">Affected Commuters</span>
                <span className="font-bold text-[var(--color-accent)] text-3xl relative z-10 mb-2">{localData.economic_impact.affected_commuters?.toLocaleString()}</span>
                <span className="text-sm text-[var(--color-text-muted)] text-center leading-relaxed max-w-[90%]">Projected number of individuals directly impacted across the network.</span>
              </div>

              <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center items-center shadow-2xl relative group">
                <InfoTooltip text="Estimated from predicted congestion volume applying a fixed per-incident fuel burn rate." />
                <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 relative z-10">Fuel Wasted</span>
                <span className="font-bold text-[var(--color-accent)] text-3xl relative z-10 mb-2">{localData.economic_impact.fuel_liters_wasted?.toLocaleString()} L</span>
                <span className="text-sm text-[var(--color-text-muted)] text-center leading-relaxed max-w-[90%]">Estimated excess fuel burn caused by heavy idling in congestion zones.</span>
                {localData.economic_impact.surcharge_lakhs > 0 && (
                  <div className="mt-3 bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/20 px-3 py-1.5 rounded text-[10px] text-[var(--color-accent)] font-bold text-center leading-tight w-full relative z-10">
                    {localData.economic_impact.surcharge_recommendation.replace('HIGH IMPACT: ', '').replace('MEDIUM IMPACT: ', '')}
                  </div>
                )}
              </div>
            </div>
          </div>
      )}
    </div>
  );
};
