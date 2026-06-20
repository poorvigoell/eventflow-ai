import { Navigation, Maximize2, Minimize2, Map as MapIcon, Loader2, AlertTriangle, TrendingUp, Activity, Search, Info } from 'lucide-react';
import { TimelineChart } from './TimelineChart';
import MapOverlay from './MapOverlay';
import Legend from './Legend';
import { useState, useEffect } from 'react';

const CustomSelect = ({ value, onChange, options }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-full bg-[var(--color-base)] border border-[var(--color-border)] rounded-lg p-3 text-left text-[var(--color-text-main)] flex justify-between items-center hover:bg-[var(--color-surface-hover)] transition-colors"
      >
        <span className="font-semibold">{options.find(o => o.value === value)?.label}</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}><path d="m6 9 6 6 6-6" /></svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-2xl z-[100] overflow-hidden">
          {options.map(o => (
            <div
              key={o.value}
              onClick={() => { onChange(o.value); setOpen(false); }}
              className="p-3 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-accent)]/20 hover:text-[var(--color-text-main)] cursor-pointer transition-colors border-b border-[var(--color-border)] last:border-0 font-medium"
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
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
)

export function LiveDashboard({
  data, loading,
  eventType, setEventType,
  duration, setDuration,
  startTime, setStartTime,
  rain, setRain,
  emergency, setEmergency,
  multiEvent, setMultiEvent,
  lat, lng, setLat, setLng,
  showPin, setShowPin,
  locationName, setLocationName,
  targetBoundary, setTargetBoundary,
  analyzeEvent,
  setData,
  isFullscreen, setIsFullscreen,
  initialMapData
}) {
  const [showBaseline, setShowBaseline] = useState(false);
  const [tomtomError, setTomtomError] = useState('');

  // Fetch TomTom baseline when toggled
  useEffect(() => {
    const runFetch = async () => {
      try {
        setTomtomError('');
        const res = await fetch(`http://localhost:8000/api/external/tomtom/flows?lat=${lat}&lng=${lng}&num_roads=5`);
        const payload = await res.json();
        if (!res.ok) {
          setTomtomError(payload?.detail || payload?.message || 'TomTom fetch failed');
          return;
        }
        if (!payload.mock) {
          window.dispatchEvent(new CustomEvent('externalTraffic', { detail: { flow: payload.data } }));
        } else {
          setTomtomError(payload.message || 'TomTom fallback active');
        }
      } catch (err) { 
        console.error('TomTom fetch error', err); 
        setTomtomError('Unable to contact TomTom service.');
      }
    };
    if (showBaseline) {
      runFetch();
    } else {
      window.dispatchEvent(new CustomEvent('externalTraffic', { detail: null }));
    }
  }, [showBaseline, lat, lng]);
  useEffect(() => {
    // Force leaflet to recalculate container size on fullscreen toggle
    setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 100);
  }, [isFullscreen]);

  const eventOptions = [
    { value: 'protest', label: 'Protest/Rally' },
    { value: 'public_event', label: 'Public Concert' },
    { value: 'vip_movement', label: 'VIP Movement' },
    { value: 'sports', label: 'Cricket Match' },
  ];

  const handleSearch = async (e) => {
    if (e.key === 'Enter') {
      const query = e.target.value;
      if (!query) return;
      try {
        // Add Bengaluru to query if not present to bias results
        const searchQuery = query.toLowerCase().includes('bengaluru') || query.toLowerCase().includes('bangalore')
          ? query
          : `${query}, Bengaluru`;
        const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=1&polygon_geojson=1`);
        const data = await res.json();
        if (data && data.length > 0) {
          setLat(parseFloat(data[0].lat));
          setLng(parseFloat(data[0].lon));
          setLocationName(data[0].display_name);
          setShowPin(true);
          if (data[0].geojson) {
            setTargetBoundary(data[0].geojson);
          } else {
            setTargetBoundary(null);
          }
        } else {
          setLocationName("Location not found");
          setTargetBoundary(null);
        }
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto flex flex-col gap-6">

      {/* 1. Tracking Setup (Horizontal Bar) */}
      <div className="bg-[var(--color-surface)] p-5 rounded-xl shadow-2xl relative z-[70]">
        <div className="flex items-center gap-2 mb-4 border-b border-[var(--color-border)] pb-3">
          <Navigation className="text-[var(--color-accent)]" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Tracking Setup</h2>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-7 gap-4 items-center">
          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-[var(--color-text-muted)] mb-1.5 uppercase tracking-wide">Event Category</label>
            <CustomSelect value={eventType} onChange={setEventType} options={eventOptions} />
          </div>

          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-[var(--color-text-muted)] mb-1.5 uppercase tracking-wide">Start Time</label>
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              style={{ colorScheme: 'dark' }}
              className="w-full bg-[var(--color-base)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-[var(--color-text-main)] focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            />
          </div>

          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-[var(--color-text-muted)] mb-1.5 uppercase tracking-wide flex justify-between">
              <span>Duration</span>
              <span className="text-[var(--color-accent)]">{duration} Hours</span>
            </label>
            <input
              type="range"
              min="1" max="12" step="0.5"
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value))}
              style={{ accentColor: 'var(--color-accent)' }}
              className="w-full h-2 bg-[var(--color-base)] rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-[var(--color-text-muted)] mb-2 uppercase tracking-wide">Modifiers</label>
            <div className="flex flex-col gap-2">
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input type="checkbox" checked={rain} onChange={e => setRain(e.target.checked)} style={{ accentColor: 'var(--color-accent)' }} className="w-4 h-4 cursor-pointer" />
                <span className="text-sm font-medium group-hover:text-[var(--color-text-main)] text-[var(--color-text-muted)] transition-colors whitespace-nowrap">Rain</span>
              </label>
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input type="checkbox" checked={emergency} onChange={e => setEmergency(e.target.checked)} style={{ accentColor: 'var(--color-accent)' }} className="w-4 h-4 cursor-pointer" />
                <span className="text-sm font-medium group-hover:text-[var(--color-text-main)] text-[var(--color-text-muted)] transition-colors whitespace-nowrap">Emergency</span>
              </label>
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input type="checkbox" checked={multiEvent} onChange={e => setMultiEvent(e.target.checked)} style={{ accentColor: 'var(--color-accent)' }} className="w-4 h-4 cursor-pointer" />
                <span className="text-sm font-medium group-hover:text-[var(--color-text-main)] text-[var(--color-text-muted)] transition-colors whitespace-nowrap">Multi-Event</span>
              </label>
            </div>
          </div>

          <div className="flex flex-col h-full justify-center min-w-0 xl:col-span-2">
            <label className="block text-[10px] font-bold text-[var(--color-text-muted)] mb-1.5 uppercase tracking-wide">Location (Search or Click Map)</label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search..."
                value={locationName === 'Click a spot on the map' ? '' : locationName}
                onChange={(e) => setLocationName(e.target.value)}
                onKeyDown={handleSearch}
                className="w-full bg-[var(--color-base)] border border-[var(--color-border)] rounded-lg p-2.5 pl-8 text-sm text-[var(--color-text-main)] focus:outline-none focus:border-[var(--color-accent)] transition-colors truncate"
              />
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
            </div>
          </div>

          <div className="flex flex-col h-full justify-center">
            <button
              onClick={() => {
                console.log('Launch Prediction clicked');
                analyzeEvent();
              }}
              disabled={loading}
              type="button"
              style={{ pointerEvents: 'auto' }}
              className="w-full h-[42px] bg-[var(--color-accent)] hover:bg-[#00c853] active:opacity-75 text-[#050505] font-bold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-xs uppercase tracking-wider flex items-center justify-center gap-2"
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              {loading ? "Simulating..." : "Launch Prediction"}
            </button>
          </div>
        </div>
      </div>

      {/* 2. Map (Fixed/Fullscreen Height) */}
      <div className={`w-full overflow-hidden shadow-2xl shrink-0 ${isFullscreen ? 'fixed inset-0 z-[100] bg-[var(--color-base)] rounded-none' : 'relative rounded-xl h-[500px]'}`}>
        <div className={`absolute z-[60] flex justify-between items-center w-full p-4 pointer-events-none`}>
          <h2 className="text-sm font-bold flex items-center gap-2 bg-[var(--color-surface)]/80 backdrop-blur-md px-4 py-2 rounded-xl pointer-events-auto shadow-2xl uppercase tracking-widest text-[var(--color-text-main)]">
            <MapIcon className="text-[var(--color-accent)]" size={16} /> Live Dispatch Map
          </h2>
          <div className="flex items-center gap-3 pointer-events-auto">
            <div className="flex flex-col gap-3 w-full">
              <label className="flex items-center justify-between gap-3 bg-[var(--color-surface)]/80 hover:bg-[var(--color-surface-hover)] border border-[var(--color-border)] px-4 py-3 rounded-xl cursor-pointer transition-colors shadow-2xl backdrop-blur-md group">
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-[var(--color-text-main)] uppercase tracking-widest mb-1">Current Traffic Baseline</span>
                  <span className="text-[10px] text-[var(--color-text-muted)] group-hover:text-[var(--color-text-main)] transition-colors">Toggle real-time traffic overlay</span>
                </div>
                <div className="relative inline-flex items-center">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={showBaseline}
                    onChange={(e) => setShowBaseline(e.target.checked)}
                  />
                  <div className="w-9 h-5 bg-[var(--color-base)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[var(--color-accent)] border border-[var(--color-border)] shadow-inner"></div>
                </div>
              </label>
            </div>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="flex items-center gap-2 bg-[var(--color-surface)]/80 hover:bg-[var(--color-surface-hover)] px-3 py-2 rounded-xl transition-colors text-xs font-bold text-[var(--color-text-main)] backdrop-blur-md shadow-2xl uppercase"
            >
              {isFullscreen ? <><Minimize2 size={14} /> Exit Fullscreen</> : <><Maximize2 size={14} /> Fullscreen</>}
            </button>
          </div>
        </div>
        {tomtomError && (
          <div className="absolute left-1/2 -translate-x-1/2 top-6 z-[9999] w-auto max-w-md rounded-full border border-amber-500/50 bg-[var(--color-surface)]/95 backdrop-blur-md text-amber-500 px-5 py-2 text-xs font-bold shadow-2xl text-center">
            {tomtomError}
          </div>
        )}

        <div className="w-full h-full z-0 relative pointer-events-auto">
          <MapOverlay
            lat={lat}
            lng={lng}
            showPin={showPin}
            setLocation={(loc) => { setLat(loc.lat); setLng(loc.lng); setShowPin(true); if (setData) setData(null); }}
            locationName={locationName}
            setLocationName={(name) => { setLocationName(name); setShowPin(true); }}
            predictionData={data ? data.prediction : null}
            criticalRoads={data ? data.critical_roads : null}
            emergencyRoutes={emergency && data ? data.emergency_routes : null}
            initialMapData={initialMapData}
            targetBoundary={targetBoundary}
            setTargetBoundary={setTargetBoundary}
          />
        </div>
        <div className="mt-3 px-2">
          <Legend />
        </div>
      </div>

      {/* 3. Bottom Section: Live Analytics */}
      {!isFullscreen && (
        <div className="w-full z-10 shrink-0">
          {loading ? (
            <div className="h-[250px] bg-[var(--color-surface)] rounded-xl shadow-2xl flex flex-col items-center justify-center text-[var(--color-accent)]">
              <Loader2 size={40} className="animate-spin mb-4" />
              <h2 className="text-lg font-bold text-[var(--color-text-main)]">Simulating Dispatch Patterns...</h2>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">Calculating risk probabilities and timeline.</p>
            </div>
          ) : data ? (
            <div className="flex flex-col gap-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Timeline Chart */}
              <div className="lg:col-span-1 h-full bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] p-5 rounded-xl shadow-2xl flex flex-col min-w-0 relative overflow-hidden group">
                  <TimelineChart timelineData={data.timeline} />
              </div>

              {/* Metrics Grid */}
              <div className="lg:col-span-1 grid grid-cols-2 gap-4 min-w-0">
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-accent)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Calculated using a RandomForest ML Model trained on historical city traffic data, predicting the excess traffic volume based on event type, weather, and time of day." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 z-10">Surge</span>
                  <span className="text-4xl font-bold text-[var(--color-accent)] z-10">+{data.prediction.total_incidents}</span>
                </div>
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-accent)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Derived from the ML model's confidence rating combined with a cascading failure graph analysis of surrounding road network bottlenecks." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 z-10">Risk Score</span>
                  <span className="text-4xl font-bold text-[var(--color-accent)] z-10">{Math.round(data.prediction.confidence * 100)}</span>
                </div>
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-text-main)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Calculated dynamically using a queuing theory allocation algorithm factoring in predicted incidents and available city resources." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-accent)] uppercase tracking-widest mb-1 z-10">Dispatch Units</span>
                  <span className="text-4xl font-bold text-[var(--color-text-main)] z-10">{data.dispatch.total_units}</span>
                </div>
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] border-t-2 border-t-[var(--color-text-main)] rounded-xl p-5 flex flex-col justify-center items-center relative group shadow-2xl">
                  <InfoTooltip text="Economic impact modeling of lost person-hours due to gridlock, converted to local currency including congestion surcharges." />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-accent)]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-[var(--color-accent)] uppercase tracking-widest mb-1 z-10">Est. Cost</span>
                  <span className="text-4xl font-bold text-[var(--color-text-main)] z-10">₹{data.economic_impact.cost_lakhs}L</span>
                </div>
              </div>

              {/* Alerts & Econ */}
              <div className="lg:col-span-1 flex flex-col gap-4 min-w-[280px]">
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center relative shadow-2xl group">
                  <div className="absolute right-0 top-0 w-24 h-24 bg-[var(--color-text-muted)]/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2" />
                  <h2 className={`text-[11px] font-bold mb-2 flex items-center gap-2 uppercase tracking-widest ${
                    data.dispatch.alert_level === 'RED' ? 'text-red-500' : 
                    data.dispatch.alert_level === 'AMBER' ? 'text-amber-500' : 
                    'text-[var(--color-accent)]'
                  }`}>
                    <AlertTriangle size={16} /> {data.dispatch.alert_level}
                  </h2>
                  <p className="text-sm text-[var(--color-text-muted)] leading-relaxed font-medium">{data.dispatch.justification}</p>
                </div>

                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-start relative shadow-2xl group">
                  <InfoTooltip text="Suggested emergency services are chosen from nearby high-risk junctions and predicted incident demand." alignRight />
                  <div className="absolute right-0 top-0 w-24 h-24 bg-[var(--color-accent)]/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2" />
                  <h2 className="text-[11px] font-bold mb-3 flex items-center gap-2 text-[var(--color-accent)] uppercase tracking-widest">
                    <AlertTriangle size={16} /> Emergency Services
                  </h2>
                  <div className="flex flex-col gap-3">
                    {data.emergency_services?.map((svc, idx) => (
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
                  <span className="font-bold text-[var(--color-accent)] text-3xl relative z-10 mb-2">{data.economic_impact.person_hours} hrs</span>
                  <span className="text-sm text-[var(--color-text-muted)] text-center leading-relaxed max-w-[90%]">Total civic productivity delay estimated based on localized gridlock volume.</span>
                </div>
                
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center items-center shadow-2xl relative group">
                  <InfoTooltip text="Derived from predicted incident counts and assumed average people per vehicle in the impacted network." />
                  <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 relative z-10">Affected Commuters</span>
                  <span className="font-bold text-[var(--color-accent)] text-3xl relative z-10 mb-2">{data.economic_impact.affected_commuters?.toLocaleString()}</span>
                  <span className="text-sm text-[var(--color-text-muted)] text-center leading-relaxed max-w-[90%]">Projected number of individuals directly impacted across the network.</span>
                </div>
                
                <div className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-base)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col justify-center items-center shadow-2xl relative group">
                  <InfoTooltip text="Estimated from predicted congestion volume applying a fixed per-incident fuel burn rate." />
                  <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 relative z-10">Fuel Wasted</span>
                  <span className="font-bold text-[var(--color-accent)] text-3xl relative z-10 mb-2">{data.economic_impact.fuel_liters_wasted?.toLocaleString()} L</span>
                  <span className="text-sm text-[var(--color-text-muted)] text-center leading-relaxed max-w-[90%]">Estimated excess fuel burn caused by heavy idling in congestion zones.</span>
                  {data.economic_impact.surcharge_lakhs > 0 && (
                    <div className="mt-3 bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/20 px-3 py-1.5 rounded text-[10px] text-[var(--color-accent)] font-bold text-center leading-tight w-full relative z-10">
                      {data.economic_impact.surcharge_recommendation.replace('HIGH IMPACT: ', '').replace('MEDIUM IMPACT: ', '')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-[250px] bg-[var(--color-surface)] rounded-xl flex flex-col items-center justify-center text-[var(--color-text-muted)] shadow-2xl">
              <Activity size={32} className="mb-3 opacity-50" />
              <p className="text-sm">Click "Launch Prediction" to generate real-time analytics.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
