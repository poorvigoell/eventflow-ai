import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import MapOverlay from './components/MapOverlay'
import { TimelineChart } from './components/TimelineChart'
import { SignalsTab } from './components/SignalsTab'
import { DispersalTab } from './components/DispersalTab'
import { DigitalTwin } from './components/DigitalTwin'
import { LandingPage } from './components/LandingPage'
import { Card, MetricBox, TabButton } from './components/ui/components'
import { Activity, ShieldAlert, Navigation, Maximize2, Minimize2, Map as MapIcon, ListChecks, Radio, Route, Cpu, TrendingUp, AlertTriangle, ChevronDown, Loader2 } from 'lucide-react'

import { LiveDashboard } from './components/LiveDashboard'
import { TacticalPlan } from './components/TacticalPlan'

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
  const [startTime, setStartTime] = useState(() => { 
    const d = new Date(); 
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); 
    return d.toISOString().slice(0, 16); 
  })
  const [targetBoundary, setTargetBoundary] = useState(null)
  
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
        start_time: new Date(startTime).toISOString(),
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

  const scrollContainerRef = useRef(null);

  // Reset scroll position when switching tabs
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [activeTab]);


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
        <div ref={scrollContainerRef} className={`flex-1 relative p-6 overflow-y-auto custom-scrollbar`}>
            
            {/* Main Map & Live Analytics Dashboard */}
            {activeTab === 'live' && (
              <LiveDashboard
                data={data}
                loading={loading}
                eventType={eventType} setEventType={setEventType}
                duration={duration} setDuration={setDuration}
                rain={rain} setRain={setRain}
                emergency={emergency} setEmergency={setEmergency}
                multiEvent={multiEvent} setMultiEvent={setMultiEvent}
                startTime={startTime} setStartTime={setStartTime}
                lat={lat} lng={lng} setLat={setLat} setLng={setLng}
                showPin={showPin} setShowPin={setShowPin}
                locationName={locationName} setLocationName={setLocationName}
                targetBoundary={targetBoundary} setTargetBoundary={setTargetBoundary}
                analyzeEvent={analyzeEvent}
                isFullscreen={isFullscreen} setIsFullscreen={setIsFullscreen}
                initialMapData={initialMapData}
              />
            )}

            {/* Tactical Plan Tab */}
            {activeTab === 'tactical' && (
              !data ? <EmptyState tabName="Tactical Plan" onGoLive={() => handleTabChange('live')} /> 
              : <TacticalPlan data={data} />
            )}

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
