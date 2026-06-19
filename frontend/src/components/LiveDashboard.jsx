import { Navigation, Maximize2, Minimize2, Map as MapIcon, Loader2, AlertTriangle, TrendingUp, Activity, Search, Info } from 'lucide-react';
import { TimelineChart } from './TimelineChart';
import MapOverlay from './MapOverlay';
import { useState } from 'react';

const CustomSelect = ({ value, onChange, options }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button 
        onClick={() => setOpen(!open)}
        className="w-full bg-[#111] border border-white/10 rounded-lg p-3 text-left text-white flex justify-between items-center hover:bg-[#222] transition-colors"
      >
        <span className="font-semibold">{options.find(o => o.value === value)?.label}</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}><path d="m6 9 6 6 6-6"/></svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1a1a] border border-white/10 rounded-lg shadow-2xl z-[100] overflow-hidden">
          {options.map(o => (
            <div 
              key={o.value}
              onClick={() => { onChange(o.value); setOpen(false); }}
              className="p-3 text-sm text-gray-200 hover:bg-[#00d2ff]/20 hover:text-white cursor-pointer transition-colors border-b border-white/5 last:border-0 font-medium"
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

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
  isFullscreen, setIsFullscreen,
  initialMapData
}) {
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
      <div className="bg-[#111] border border-white/10 p-5 rounded-2xl shadow-xl relative z-[70]">
        <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-3">
          <Navigation className="text-[#00d2ff]" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-300">Tracking Setup</h2>
        </div>
        
        <div className="grid grid-cols-1 xl:grid-cols-7 gap-4 items-center">
          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-gray-400 mb-1.5 uppercase tracking-wide">Event Category</label>
            <CustomSelect value={eventType} onChange={setEventType} options={eventOptions} />
          </div>

          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-gray-400 mb-1.5 uppercase tracking-wide">Start Time</label>
            <input 
              type="datetime-local" 
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full bg-[#111] border border-white/10 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[#00d2ff] transition-colors"
            />
          </div>

          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-gray-400 mb-1.5 uppercase tracking-wide flex justify-between">
              <span>Duration</span>
              <span className="text-[#00d2ff]">{duration} Hours</span>
            </label>
            <input 
              type="range" 
              min="1" max="12" step="0.5" 
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value))}
              className="w-full accent-[#00d2ff] h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer" 
            />
          </div>

          <div className="flex flex-col h-full justify-center">
            <label className="block text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-wide">Modifiers</label>
            <div className="flex flex-col gap-2">
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input type="checkbox" checked={rain} onChange={e => setRain(e.target.checked)} className="accent-[#00d2ff] w-4 h-4 cursor-pointer" />
                <span className="text-sm font-medium group-hover:text-white text-gray-400 transition-colors whitespace-nowrap">Rain</span>
              </label>
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input type="checkbox" checked={emergency} onChange={e => setEmergency(e.target.checked)} className="accent-[#00e676] w-4 h-4 cursor-pointer" />
                <span className="text-sm font-medium group-hover:text-white text-gray-400 transition-colors whitespace-nowrap">Emergency</span>
              </label>
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input type="checkbox" checked={multiEvent} onChange={e => setMultiEvent(e.target.checked)} className="accent-[#ff4b2b] w-4 h-4 cursor-pointer" />
                <span className="text-sm font-medium group-hover:text-white text-gray-400 transition-colors whitespace-nowrap">Multi-Event</span>
              </label>
            </div>
          </div>

          <div className="flex flex-col h-full justify-center min-w-0 xl:col-span-2">
            <label className="block text-[10px] font-bold text-gray-400 mb-1.5 uppercase tracking-wide">Location (Search or Click Map)</label>
            <div className="relative">
              <input 
                type="text" 
                placeholder="Search..."
                value={locationName === 'Click a spot on the map' ? '' : locationName}
                onChange={(e) => setLocationName(e.target.value)}
                onKeyDown={handleSearch}
                className="w-full bg-[#111] border border-white/10 rounded-lg p-2.5 pl-8 text-sm text-white focus:outline-none focus:border-[#00d2ff] transition-colors truncate"
              />
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
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
              className="w-full h-[42px] bg-gradient-to-r from-[#00d2ff] to-[#3a7bd5] hover:opacity-90 active:opacity-75 text-white font-bold rounded-xl shadow-[0_0_20px_rgba(0,210,255,0.2)] transition-all disabled:opacity-50 disabled:cursor-not-allowed text-xs uppercase tracking-wider flex items-center justify-center gap-2"
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              {loading ? "Simulating..." : "Launch Prediction"}
            </button>
          </div>
        </div>
      </div>

      {/* 2. Map (Fixed Height) */}
      <div className={`w-full relative rounded-2xl overflow-hidden border border-white/10 shadow-xl shrink-0 ${isFullscreen ? 'fixed inset-0 z-[100] bg-[#050505] rounded-none' : 'h-[500px]'}`}>
        <div className={`absolute z-[60] flex justify-between items-center w-full p-4 pointer-events-none`}>
          <h2 className="text-sm font-black flex items-center gap-2 bg-black/60 backdrop-blur-md px-4 py-2 rounded-xl pointer-events-auto border border-white/10 shadow-xl uppercase tracking-widest">
            <MapIcon className="text-[#00d2ff]" size={16} /> Live Dispatch Map
          </h2>
          <button 
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center gap-2 bg-[#111]/80 hover:bg-[#222] px-3 py-2 rounded-xl border border-white/20 transition-colors text-xs font-bold text-gray-300 backdrop-blur-md shadow-xl pointer-events-auto uppercase"
          >
            {isFullscreen ? <><Minimize2 size={14}/> Exit Fullscreen</> : <><Maximize2 size={14}/> Fullscreen</>}
          </button>
        </div>

        <div className="w-full h-full z-0 relative pointer-events-auto">
          <MapOverlay 
            lat={lat} 
            lng={lng} 
            showPin={showPin}
            setLocation={(loc) => { setLat(loc.lat); setLng(loc.lng); setShowPin(true); }}
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
      </div>

      {/* 3. Bottom Section: Live Analytics */}
      {!isFullscreen && (
        <div className="w-full z-10 shrink-0">
          {loading ? (
            <div className="h-[250px] bg-[#111] border border-white/5 rounded-2xl flex flex-col items-center justify-center text-[#00d2ff]">
              <Loader2 size={40} className="animate-spin mb-4" />
              <h2 className="text-lg font-bold">Simulating Dispatch Patterns...</h2>
              <p className="text-sm text-gray-500">Calculating risk probabilities and timeline.</p>
            </div>
          ) : data ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Timeline Chart */}
              <div className="lg:col-span-1 bg-[#111] p-5 rounded-2xl border border-white/5 flex flex-col min-w-0 shadow-xl">
                <TimelineChart timelineData={data.timeline} />
              </div>
              
              {/* Metrics Grid */}
              <div className="lg:col-span-1 grid grid-cols-2 gap-4 min-w-0">
                <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
                  <div className="absolute top-2 left-2 text-gray-500 hover:text-white cursor-help z-50">
                    <Info size={12} />
                    <div className="hidden group-hover:block absolute top-full left-0 mt-1 w-48 p-2 bg-[#1a1a1a] border border-white/10 rounded shadow-xl text-[10px] text-left text-gray-300 z-50 normal-case tracking-normal font-medium">
                      Calculated using a RandomForest ML Model trained on historical city traffic data, predicting the excess traffic volume based on event type, weather, and time of day.
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-t from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Surge</span>
                  <span className="text-4xl font-black text-red-400 z-10">+{data.prediction.total_incidents}</span>
                </div>
                <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
                  <div className="absolute top-2 left-2 text-gray-500 hover:text-white cursor-help z-50">
                    <Info size={12} />
                    <div className="hidden group-hover:block absolute top-full left-0 mt-1 w-48 p-2 bg-[#1a1a1a] border border-white/10 rounded shadow-xl text-[10px] text-left text-gray-300 z-50 normal-case tracking-normal font-medium">
                      Derived from the ML model's confidence rating combined with a cascading failure graph analysis of surrounding road network bottlenecks.
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-t from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Risk Score</span>
                  <span className="text-4xl font-black text-orange-400 z-10">{Math.round(data.prediction.confidence * 100)}</span>
                </div>
                <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
                  <div className="absolute top-2 left-2 text-gray-500 hover:text-white cursor-help z-50">
                    <Info size={12} />
                    <div className="hidden group-hover:block absolute top-full left-0 mt-1 w-48 p-2 bg-[#1a1a1a] border border-white/10 rounded shadow-xl text-[10px] text-left text-gray-300 z-50 normal-case tracking-normal font-medium">
                      Calculated dynamically using a queuing theory allocation algorithm factoring in predicted incidents and available city resources.
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-t from-[#00d2ff]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Dispatch Units</span>
                  <span className="text-4xl font-black text-[#00d2ff] z-10">{data.dispatch.total_units}</span>
                </div>
                <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
                  <div className="absolute top-2 right-2 text-gray-500 hover:text-white cursor-help z-50">
                    <Info size={12} />
                    <div className="hidden group-hover:block absolute top-full right-0 mt-1 w-48 p-2 bg-[#1a1a1a] border border-white/10 rounded shadow-xl text-[10px] text-left text-gray-300 z-50 normal-case tracking-normal font-medium">
                      Economic impact modeling of lost person-hours due to gridlock, converted to local currency including congestion surcharges.
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-t from-[#c77dff]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Est. Cost</span>
                  <span className="text-4xl font-black text-[#c77dff] z-10">₹{data.economic_impact.cost_lakhs}L</span>
                </div>
              </div>
              
              {/* Alerts & Econ */}
              <div className="lg:col-span-1 flex flex-col gap-4 min-w-[280px]">
                <div className="flex-1 bg-gradient-to-br from-red-500/10 to-[#111] border border-red-500/20 rounded-2xl p-5 flex flex-col justify-center relative overflow-hidden shadow-xl">
                  <div className="absolute right-0 top-0 w-24 h-24 bg-red-500/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2" />
                  <h2 className="text-[11px] font-black mb-2 flex items-center gap-2 text-red-400 uppercase tracking-widest">
                    <AlertTriangle size={16} /> {data.dispatch.alert_level}
                  </h2>
                  <p className="text-sm text-gray-300 leading-relaxed font-medium">{data.dispatch.justification}</p>
                </div>
                
                <div className="flex-1 bg-gradient-to-br from-[#c77dff]/10 to-[#111] border border-[#c77dff]/20 rounded-2xl p-5 flex flex-col justify-center relative overflow-hidden shadow-xl">
                  <div className="absolute right-0 top-0 w-24 h-24 bg-[#c77dff]/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2" />
                  <h2 className="text-[11px] font-black mb-3 flex items-center gap-2 text-[#c77dff] uppercase tracking-widest">
                    <TrendingUp size={16} /> Impact Summary
                  </h2>
                  <div className="flex justify-between items-center text-sm mb-1">
                    <span className="text-gray-400 uppercase tracking-wider font-bold">Hours Lost</span>
                    <span className="font-black text-white text-xl">{data.economic_impact.person_hours}h</span>
                  </div>
                  {data.economic_impact.surcharge_lakhs > 0 && (
                    <div className="text-[11px] text-[#ffbb00] mt-2 font-mono bg-[#ffbb00]/10 px-2.5 py-1.5 rounded-lg inline-block border border-[#ffbb00]/20 font-bold">
                      Surcharge: {data.economic_impact.surcharge_recommendation}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-[250px] bg-[#111] border border-white/5 rounded-2xl flex flex-col items-center justify-center text-gray-600">
              <Activity size={32} className="mb-3 opacity-50" />
              <p className="text-sm">Click "Launch Prediction" to generate real-time analytics.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
