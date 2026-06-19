import { useState, useEffect } from 'react'
import axios from 'axios'
import MapOverlay from './components/MapOverlay'
import { TimelineChart } from './components/TimelineChart'
import { SignalsTab } from './components/SignalsTab'
import { DispersalTab } from './components/DispersalTab'
import { DigitalTwin } from './components/DigitalTwin'
import { LandingPage } from './components/LandingPage'
import { Card, MetricBox, TabButton } from './components/ui/components'
import { Activity, ShieldAlert, Navigation, Maximize2, Minimize2, Map as MapIcon, ListChecks, Radio, Route, Cpu, TrendingUp, AlertTriangle, ChevronDown, Loader2 } from 'lucide-react'

const CustomSelect = ({ value, onChange, options }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button 
        onClick={() => setOpen(!open)}
        className="w-full bg-[#111] border border-white/10 rounded-lg p-3 text-left text-white flex justify-between items-center hover:bg-[#222] transition-colors"
      >
        <span className="font-semibold">{options.find(o => o.value === value)?.label}</span>
        <ChevronDown size={16} className={`text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
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

const EmptyState = ({ tabName, onGoLive }) => (
  <div className="flex flex-col items-center justify-center h-[500px] text-gray-500 bg-[#111] border border-white/5 rounded-2xl max-w-4xl mx-auto mt-10 shadow-xl">
    <Activity size={48} className="mb-4 opacity-50 text-[#00d2ff]" />
    <h2 className="text-xl font-bold text-gray-300 mb-2">No Data Loaded for {tabName}</h2>
    <p className="text-sm">Please launch a prediction on the Live Dashboard first to view analytics.</p>
    <button onClick={onGoLive} className="mt-6 px-6 py-2 bg-[#00d2ff]/10 text-[#00d2ff] rounded-xl hover:bg-[#00d2ff]/20 font-bold text-sm transition-colors border border-[#00d2ff]/20 uppercase tracking-wider">
      Go to Live Dashboard
    </button>
  </div>
);

function App() {
  const initialHash = window.location.hash.replace('#', '')
  const validTabs = ['live', 'tactical', 'signals', 'dispersal', 'twin']
  const startingTab = validTabs.includes(initialHash) ? initialHash : 'live'
  
  const [showLanding, setShowLanding] = useState(!initialHash)
  const [lat, setLat] = useState(12.9788)
  const [lng, setLng] = useState(77.5996)
  const [showPin, setShowPin] = useState(false)
  const [locationName, setLocationName] = useState('Click a spot on the map')
  const [eventType, setEventType] = useState('protest')
  const [duration, setDuration] = useState(4)
  const [rain, setRain] = useState(false)
  const [emergency, setEmergency] = useState(false)
  const [multiEvent, setMultiEvent] = useState(false)
  
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [initialMapData, setInitialMapData] = useState(null)
  
  const [activeTab, setActiveTab] = useState(startingTab)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Fetch initial POIs on mount
  useEffect(() => {
    axios.get('http://localhost:8000/api/initial-map-data')
      .then(res => setInitialMapData(res.data))
      .catch(err => console.error(err))
  }, [])

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    window.location.hash = tab
  }

  const analyzeEvent = async () => {
    setLoading(true)
    setData(null) // Clear previous analytics
    try {
      const response = await axios.post('http://localhost:8000/api/predict', {
        event_type: eventType,
        latitude: lat,
        longitude: lng,
        zone: "Central",
        start_time: new Date().toISOString(),
        duration_hours: duration,
        weather_rain: rain,
        multi_event_mode: multiEvent,
        emergency_mode: emergency
      })
      setData(response.data)
    } catch (error) {
      console.error("Error fetching data:", error)
    }
    setLoading(false)
  }

  if (showLanding) {
    return <LandingPage onEnter={() => {
      setShowLanding(false)
      window.location.hash = 'live'
    }} />;
  }

  const eventOptions = [
    { value: 'protest', label: 'Protest/Rally' },
    { value: 'public_event', label: 'Public Concert' },
    { value: 'vip_movement', label: 'VIP Movement' },
    { value: 'sports', label: 'Cricket Match' },
  ];

  return (
    <div className="flex flex-col h-screen bg-[#050505] text-white font-sans overflow-hidden">
      
      {/* Global Top Navbar */}
      <nav className="flex items-center justify-between px-6 bg-[#0a0a0a] border-b border-white/10 shrink-0 h-16 z-50 relative">
        <div className="flex items-center gap-4">
          <Activity className="text-[#00d2ff]" size={24} />
          <h1 className="text-xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-[#00d2ff] to-[#3a7bd5]">
            EventFlow AI
          </h1>
        </div>
        
        {/* Tabs moved to Navbar */}
        <div className="flex items-center h-full gap-2">
          <TabButton active={activeTab === 'live'} onClick={() => handleTabChange('live')} icon={<Activity size={18}/>} label="Live Dashboard" />
          <TabButton active={activeTab === 'tactical'} onClick={() => handleTabChange('tactical')} icon={<ListChecks size={18}/>} label="Tactical Plan" />
          <TabButton active={activeTab === 'signals'} onClick={() => handleTabChange('signals')} icon={<Radio size={18}/>} label="Signals" />
          <TabButton active={activeTab === 'dispersal'} onClick={() => handleTabChange('dispersal')} icon={<Route size={18}/>} label="Crowd Dispersal" />
          <TabButton active={activeTab === 'twin'} onClick={() => handleTabChange('twin')} icon={<Cpu size={18}/>} label="Digital Twin" />
        </div>
        
        <div className="flex items-center gap-4">
          <button onClick={() => setShowLanding(true)} className="text-xs text-gray-400 hover:text-white transition-colors">Exit</button>
        </div>
      </nav>

      {/* Main Dashboard Area */}
      <div className="flex flex-1 overflow-hidden relative bg-[#080808]">
        
        {/* Main Content Area (Map / Tabs) */}
        <div className={`flex-1 relative p-6 overflow-y-auto custom-scrollbar`}>
            
            {/* Main Map & Live Analytics Dashboard */}
            {activeTab === 'live' && (
              <div className="max-w-[1400px] mx-auto flex flex-col gap-6">
                
                {/* 1. Tracking Setup (Horizontal Bar) */}
                <div className="bg-[#111] border border-white/10 p-5 rounded-2xl shadow-xl z-10">
                  <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-3">
                    <Navigation className="text-[#00d2ff]" size={18} />
                    <h2 className="text-sm font-bold uppercase tracking-wider text-gray-300">Tracking Setup</h2>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
                    <div className="flex flex-col h-full justify-center">
                      <label className="block text-[10px] font-bold text-gray-400 mb-1.5 uppercase tracking-wide">Event Category</label>
                      <CustomSelect value={eventType} onChange={setEventType} options={eventOptions} />
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
                      <label className="block text-[10px] font-bold text-gray-400 mb-1.5 uppercase tracking-wide">Modifiers</label>
                      <div className="flex flex-wrap gap-x-4 gap-y-2">
                        <label className="flex items-center gap-1.5 cursor-pointer group">
                          <input type="checkbox" checked={rain} onChange={e => setRain(e.target.checked)} className="accent-[#00d2ff] w-3.5 h-3.5 cursor-pointer" />
                          <span className="text-xs group-hover:text-white text-gray-400 transition-colors whitespace-nowrap">Heavy Rain</span>
                        </label>
                        <label className="flex items-center gap-1.5 cursor-pointer group">
                          <input type="checkbox" checked={emergency} onChange={e => setEmergency(e.target.checked)} className="accent-[#00e676] w-3.5 h-3.5 cursor-pointer" />
                          <span className="text-xs group-hover:text-white text-gray-400 transition-colors whitespace-nowrap">Emergency</span>
                        </label>
                        <label className="flex items-center gap-1.5 cursor-pointer group">
                          <input type="checkbox" checked={multiEvent} onChange={e => setMultiEvent(e.target.checked)} className="accent-[#ff4b2b] w-3.5 h-3.5 cursor-pointer" />
                          <span className="text-xs group-hover:text-white text-gray-400 transition-colors whitespace-nowrap">Multi-Event</span>
                        </label>
                      </div>
                    </div>

                    <div className="p-2.5 bg-[#0a0a0a] rounded-xl border border-white/5 flex flex-col justify-center min-w-0">
                      <p className="text-[9px] text-gray-500 uppercase tracking-widest mb-0.5">Target (Click Map)</p>
                      <p className="text-xs text-[#00d2ff] font-bold truncate" title={locationName}>{locationName}</p>
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

                  <div className="w-full h-full z-0 relative">
                    <MapOverlay 
                      lat={lat} 
                      lng={lng} 
                      showPin={showPin}
                      setLocation={(loc) => { setLat(loc.lat); setLng(loc.lng); setShowPin(true); }}
                      locationName={locationName}
                      setLocationName={(name) => { setLocationName(name); setShowPin(true); }}
                      predictionData={data ? data.prediction : null}
                      criticalRoads={data ? data.critical_roads : null}
                      initialMapData={initialMapData}
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
                            <div className="absolute inset-0 bg-gradient-to-t from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Surge</span>
                            <span className="text-4xl font-black text-red-400 z-10">+{data.prediction.total_incidents}</span>
                          </div>
                          <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
                            <div className="absolute inset-0 bg-gradient-to-t from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Risk Score</span>
                            <span className="text-4xl font-black text-orange-400 z-10">{Math.round(data.prediction.confidence * 100)}</span>
                          </div>
                          <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
                            <div className="absolute inset-0 bg-gradient-to-t from-[#00d2ff]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1 z-10">Dispatch Units</span>
                            <span className="text-4xl font-black text-[#00d2ff] z-10">{data.dispatch.total_units}</span>
                          </div>
                          <div className="bg-[#111] border border-white/5 rounded-2xl p-5 flex flex-col justify-center items-center relative overflow-hidden group shadow-xl">
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
            )}

            {/* Tactical Plan Tab */}
            {activeTab === 'tactical' && (!data ? <EmptyState tabName="Tactical Plan" onGoLive={() => handleTabChange('live')} /> : (
              <div className="max-w-4xl mx-auto space-y-6 pb-20">
                <h2 className="text-2xl font-black mb-6 flex items-center gap-2 border-b border-white/10 pb-4">
                  <ShieldAlert className="text-[#00d2ff]" size={28}/> Tactical Deployment Plan
                </h2>
                
                <div className="grid grid-cols-5 gap-4">
                  <MetricBox title="Police" value={data.tactical.manpower.traffic_police} colorClass="text-[#00d2ff] bg-blue-500/10" subtitle="👮" />
                  <MetricBox title="Patrols" value={data.tactical.manpower.patrol_vehicles} colorClass="text-[#3a7bd5] bg-blue-600/10" subtitle="🚓" />
                  <MetricBox title="Ambulance" value={data.tactical.manpower.ambulances} colorClass="text-[#00e676] bg-green-500/10" subtitle="🚑" />
                  <MetricBox title="Tow Trucks" value={data.tactical.manpower.tow_trucks} colorClass="text-[#ffbb00] bg-yellow-500/10" subtitle="🚜" />
                  <MetricBox title="Barricades" value={data.tactical.manpower.barricade_teams} colorClass="text-[#ff4b2b] bg-red-500/10" subtitle="🚧" />
                </div>

                <div className="grid grid-cols-2 gap-6 mt-8">
                  <Card>
                    <h3 className="text-lg font-bold text-[#ff4b2b] mb-4">🚧 Active Barricade Protocol</h3>
                    <div className="space-y-3">
                      {data.tactical.barricade_roads?.map((road, i) => (
                        <div key={i} className="bg-red-500/5 border border-red-500/20 p-3 rounded-lg flex flex-col gap-1">
                          <div className="flex justify-between items-start">
                            <span className="font-semibold text-white">{road.road}</span>
                            <span className="text-[10px] bg-red-500 text-white px-2 py-0.5 rounded uppercase font-bold">{road.timing}</span>
                          </div>
                          <span className="text-xs text-gray-400">{road.reason}</span>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <Card>
                    <h3 className="text-lg font-bold text-[#00d2ff] mb-4">🧭 Routing & Diversion Protocol</h3>
                    <div className="space-y-3">
                      {data.tactical.diversion_plan?.length > 0 ? (
                        data.tactical.diversion_plan.map((div, i) => (
                          <div key={i} className="bg-blue-500/5 border border-blue-500/20 p-3 rounded-lg">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-bold text-gray-300">Alternate Route</span>
                              <span className="text-xs text-[#00d2ff] font-mono">{div.added_time} delay</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <span className="line-through text-red-400">{div.from}</span>
                              <span className="text-gray-500">→</span>
                              <span className="text-[#00e676] font-bold">via {div.via}</span>
                              <span className="text-gray-500">→</span>
                              <span className="text-white">{div.to}</span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="flex flex-col items-center justify-center p-8 text-gray-500 bg-blue-500/5 rounded-lg border border-blue-500/10 h-full">
                          <MapIcon className="mb-3 opacity-50 text-[#00d2ff]" size={32} />
                          <p className="text-sm font-bold text-gray-400">No Diversions Needed</p>
                          <p className="text-xs text-center mt-1 text-gray-500">Traffic flow remains within capacity parameters.</p>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            ))}

            {/* Signals Tab */}
            {activeTab === 'signals' && (!data ? <EmptyState tabName="Signals" onGoLive={() => handleTabChange('live')} /> : <SignalsTab signals={data?.signals} />)}

            {/* Dispersal Tab */}
            {activeTab === 'dispersal' && (!data ? <EmptyState tabName="Crowd Dispersal" onGoLive={() => handleTabChange('live')} /> : (
              <DispersalTab 
                lat={lat} 
                lng={lng} 
                eventType={eventType} 
                totalIncidents={data.prediction.total_incidents} 
              />
            ))}

            {/* Digital Twin Tab */}
            {activeTab === 'twin' && (!data ? <EmptyState tabName="Digital Twin" onGoLive={() => handleTabChange('live')} /> : (
              <DigitalTwin 
                lat={lat} 
                lng={lng} 
                predictionData={data.prediction} 
              />
            ))}

        </div>
      </div>
    </div>
  )
}

export default App
