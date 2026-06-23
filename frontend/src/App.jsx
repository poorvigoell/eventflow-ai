import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { SignalsTab } from './components/SignalsTab'
import { DispersalTab } from './components/DispersalTab'
import { AutopsyTab } from './components/AutopsyTab'
import { DigitalTwin } from './components/DigitalTwin'
import { AlertsTab } from './components/AlertsTab'
import { LandingPage } from './components/LandingPage'
import { TabButton } from './components/ui/components'
import { Activity, ListChecks, Radio, Route, Cpu, AlertTriangle, Bell, FileSearch } from 'lucide-react'

import { PredictionDashboard } from './components/PredictionDashboard'
import { TacticalPlan } from './components/TacticalPlan'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React Render Error Caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen bg-[#0A0A0A] text-red-500 p-8 text-center font-mono">
          <AlertTriangle size={64} className="mb-6" />
          <h1 className="text-3xl font-bold mb-4 text-white">Oops! The application crashed.</h1>
          <p className="text-gray-400 mb-8 max-w-2xl">A rendering error occurred in one of the components. The error has been caught to prevent a completely blank screen.</p>
          <div className="bg-red-900/20 border border-red-500/50 p-4 rounded text-left max-w-4xl overflow-auto text-sm">
            <code>{this.state.error?.toString()}</code>
          </div>
          <button onClick={() => window.location.reload()} className="mt-8 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition-colors">
            Reload Application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const EmptyState = ({ tabName, onGoLive }) => (
  <div className="flex flex-col items-center justify-center h-[500px] text-[var(--color-text-muted)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl max-w-4xl mx-auto mt-10 shadow-2xl">
    <Activity size={48} className="mb-4 opacity-50 text-[var(--color-accent)]" />
    <h2 className="text-xl font-bold text-[var(--color-text-main)] mb-2">No Data Loaded for {tabName}</h2>
    <p className="text-sm">Please launch a prediction on the Live Dashboard first to view analytics.</p>
    <button onClick={onGoLive} className="mt-6 px-6 py-2 bg-[var(--color-accent)]/10 text-[var(--color-accent)] rounded-xl hover:bg-[var(--color-accent)]/20 font-bold text-sm transition-colors border border-[var(--color-accent)]/20 uppercase tracking-wider">
      Go to Live Dashboard
    </button>
  </div>
);

const CACHE_KEY = 'eventflow_app_state';
const CACHE_EXPIRY_MS = 30 * 60 * 1000;

function App() {
  // Load cached state using useState initializer to avoid purity violation
  const [cachedState] = useState(() => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Date.now() - parsed.timestamp < CACHE_EXPIRY_MS) {
          const s = parsed.state;
          // Validate coordinates — discard cache if corrupted
          const lat = s?.lat;
          const lng = s?.lng;
          if (typeof lat !== 'number' || isNaN(lat) || typeof lng !== 'number' || isNaN(lng)) {
            localStorage.removeItem(CACHE_KEY);
            return null;
          }
          return s;
        }
      }
    } catch {
      // Ignore cache parsing errors
    }
    return null;
  });


  const initialHash = window.location.hash.replace('#', '')
  const validTabs = ['live', 'tactical', 'signals', 'dispersal', 'twin', 'autopsy', 'alerts']
  const startingTab = validTabs.includes(initialHash) ? initialHash : 'live'

  const [showLanding, setShowLanding] = useState(!initialHash)
  
  const [lat, setLat] = useState(cachedState?.lat ?? 12.9788)
  const [lng, setLng] = useState(cachedState?.lng ?? 77.5996)
  const [showPin, setShowPin] = useState(cachedState?.showPin ?? false)
  const [locationName, setLocationName] = useState(cachedState?.locationName ?? 'Click a spot on the map')
  const [eventType, setEventType] = useState(cachedState?.eventType ?? 'protest')
  const [duration, setDuration] = useState(cachedState?.duration ?? 4)
  const [rain, setRain] = useState(cachedState?.rain ?? false)
  const [emergency, setEmergency] = useState(cachedState?.emergency ?? false)
  const [multiEvent, setMultiEvent] = useState(cachedState?.multiEvent ?? false)
  const [startTime, setStartTime] = useState(cachedState?.startTime ?? (() => {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  }))
  const [targetBoundary, setTargetBoundary] = useState(cachedState?.targetBoundary ?? null)

  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(cachedState?.data ?? null)
  const [initialMapData, setInitialMapData] = useState(null)

  const [activeTab, setActiveTab] = useState(startingTab)
  const activeTabRef = useRef(activeTab)
  const [visitedTabs, setVisitedTabs] = useState(() => {
    const fromCache = cachedState?.visitedTabs;
    return fromCache ? [...new Set([startingTab, ...fromCache])] : [startingTab];
  })
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [activeAnalysisSource, setActiveAnalysisSource] = useState(cachedState?.activeAnalysisSource ?? null)

  const [anomalies, setAnomalies] = useState([])
  const [toast, setToast] = useState(null)
  
  const hasActiveAnomalies = anomalies.some(a => a.status === 'active')

  // Fetch initial anomalies
  useEffect(() => {
    axios.get('http://localhost:8000/api/traffic/anomalies')
      .then(res => setAnomalies(res.data))
      .catch(err => console.error(err))
  }, [])

  // WebSocket Connection
  useEffect(() => {
    let isMounted = true;
    let ws = null;
    let reconnectTimer = null;

    const connectWS = () => {
      ws = new WebSocket('ws://localhost:8000/ws/alerts');
      
      ws.onmessage = (event) => {
        if (!isMounted) return;
        const msg = JSON.parse(event.data);
        
        if (msg.type === 'NEW_ANOMALY') {
          setAnomalies(prev => {
            // Prevent duplicate anomalies from being added
            if (prev.some(a => a.id === msg.data.id)) return prev;
            return [msg.data, ...prev];
          });
          setToast(`🚨 Severe Gridlock Detected at ${msg.data.junction}!`);
          setTimeout(() => setToast(null), 5000);
        } else if (msg.type === 'ANOMALY_RESOLVED') {
          setAnomalies(prev => prev.map(a => 
            a.id === msg.anomaly_id ? { ...a, status: 'resolved', resolved_at: msg.resolved_at } : a
          ));
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          console.log('WebSocket closed, reconnecting in 2s...');
          reconnectTimer = setTimeout(connectWS, 2000);
        }
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
      };
    };

    connectWS();

    return () => {
      isMounted = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  useEffect(() => {
    activeTabRef.current = activeTab;
  }, [activeTab]);

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    window.location.hash = tab
    if (!visitedTabs.includes(tab)) {
      setVisitedTabs(prev => [...prev, tab]);
    }
  }

  const analyzeEvent = async () => {
    if (!showPin) {
      window.alert("Please select a location on the map to continue.");
      return;
    }
    setLoading(true)
    setData(null) // Clear previous analytics
    setActiveAnalysisSource('prediction_setup')
    try {
      console.log("Sending prediction request...");
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
      }, { timeout: 60000 })
      console.log("Prediction response received", response.data);
      setData(response.data)
    } catch (error) {
      console.error("Error fetching data:", error)
      const msg = error.response?.data?.detail || error.message;
      window.alert(`Simulation failed: ${msg}. Please check the backend logs.`);
    } finally {
      setLoading(false)
    }
  }

  // Save to cache whenever relevant state changes
  useEffect(() => {
    const stateToCache = {
      lat, lng, showPin, locationName, eventType, duration, rain, emergency, multiEvent, startTime, targetBoundary,
      data, activeAnalysisSource, visitedTabs
    };
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        timestamp: Date.now(),
        state: stateToCache
      }));
    } catch (e) {
      // Ignore quota errors
      console.warn('Cache write failed:', e);
    }
  }, [lat, lng, showPin, locationName, eventType, duration, rain, emergency, multiEvent, startTime, targetBoundary, data, activeAnalysisSource, visitedTabs]);

  // Fetch initial POIs on mount
  useEffect(() => {
    axios.get('http://localhost:8000/api/initial-map-data')
      .then(res => setInitialMapData(res.data))
      .catch(err => console.error(err))
  }, [])

  const scrollContainerRef = useRef(null);

  // Reset scroll position when switching tabs
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [activeTab]);

  if (showLanding) {
    return <LandingPage onEnter={() => {
      setShowLanding(false)
      window.location.hash = 'live'
    }} />;
  }


  return (
    <div className="flex flex-col h-screen bg-[var(--color-base)] text-[var(--color-text-main)] font-sans overflow-hidden relative">

      {/* Global Toast Notification */}
      {toast && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-50 bg-red-500/90 border border-red-500 text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 animate-in slide-in-from-top-4 fade-in duration-300">
          <AlertTriangle size={20} />
          <span className="font-bold">{toast}</span>
        </div>
      )}

      {/* Global Top Navbar */}
      <nav className="flex items-center justify-between px-6 bg-[var(--color-surface)] border-b border-[var(--color-border)] shrink-0 h-16 z-50 relative">
        <div className="flex items-center gap-4">
          <Activity className="text-[var(--color-accent)]" size={24} />
          <h1 className="text-xl font-bold text-[var(--color-text-main)]">
            EventFlow
          </h1>
        </div>

        {/* Tabs moved to Navbar */}
        <div className="flex items-center h-full gap-2">
          <TabButton active={activeTab === 'live'} onClick={() => handleTabChange('live')} icon={<Activity size={18} />} label="Prediction Setup" />
          <div className="relative">
            <TabButton active={activeTab === 'alerts'} onClick={() => handleTabChange('alerts')} icon={<Bell size={18} />} label="Live Traffic" />
            {hasActiveAnomalies && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[var(--color-surface)] animate-pulse" />
            )}
          </div>
          <TabButton active={activeTab === 'tactical'} onClick={() => handleTabChange('tactical')} icon={<ListChecks size={18} />} label="Tactical Plan" />
          <TabButton active={activeTab === 'signals'} onClick={() => handleTabChange('signals')} icon={<Radio size={18} />} label="Signals" />
          <TabButton active={activeTab === 'dispersal'} onClick={() => handleTabChange('dispersal')} icon={<Route size={18} />} label="Crowd Dispersal" />
          <TabButton active={activeTab === 'autopsy'} onClick={() => handleTabChange('autopsy')} icon={<FileSearch size={18} />} label="Causal Autopsy" />
          <div className="flex-grow"></div>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={() => setShowLanding(true)} className="text-xs text-gray-400 hover:text-white transition-colors">Exit</button>
        </div>
      </nav>

      {/* Main Dashboard Area */}
      <div className="flex flex-1 overflow-hidden relative bg-[var(--color-base)]">

        {/* Main Content Area (Map / Tabs) */}
        <div ref={scrollContainerRef} className={`flex-1 relative p-6 overflow-y-auto custom-scrollbar`}>

          {/* Live Dashboard Tab */}
          <div style={{ display: activeTab === 'live' ? 'block' : 'none' }}>
            {visitedTabs.includes('live') && (
              <PredictionDashboard
                data={activeAnalysisSource === 'prediction_setup' ? data : null} loading={loading} setData={setData}
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
                anomalies={anomalies}
                activeTab={activeTab}
              />
            )}
          </div>

          {/* Tactical Plan Tab */}
          {activeTab === 'tactical' && (
            <div className="w-full h-full animate-in fade-in duration-300">
              {(!data || data.error || !data.prediction) ? <EmptyState tabName="Tactical Plan" onGoLive={() => handleTabChange('live')} />
                : <TacticalPlan data={data} lat={lat} lng={lng} predictionData={data.prediction} />}
            </div>
          )}

          {/* Signals Tab */}
          <div style={{ display: activeTab === 'signals' ? 'block' : 'none' }}>
            {visitedTabs.includes('signals') && (
              (!data || data.error || !data.prediction) ? <EmptyState tabName="Signals" onGoLive={() => handleTabChange('live')} /> 
                : <SignalsTab signals={data?.signals} eventConfig={{latitude: lat, longitude: lng, event_type: eventType, duration_hours: duration, weather_rain: rain, total_incidents: data?.prediction?.total_incidents || 0, multi_event_mode: multiEvent}} />
            )}
          </div>

          {/* Dispersal Tab */}
          <div style={{ display: activeTab === 'dispersal' ? 'block' : 'none' }}>
            {visitedTabs.includes('dispersal') && (
              (!data || data.error || !data.prediction) ? <EmptyState tabName="Crowd Dispersal" onGoLive={() => handleTabChange('live')} /> : (
                <DispersalTab
                  lat={lat}
                  lng={lng}
                  eventType={eventType}
                  totalIncidents={data.prediction.total_incidents}
                  isActive={activeTab === 'dispersal'}
                />
              )
            )}
          </div>



          {/* Autopsy Tab */}
          <div style={{ display: activeTab === 'autopsy' ? 'block' : 'none' }}>
            <AutopsyTab />
          </div>

          {/* Alerts Tab */}
          <div style={{ display: activeTab === 'alerts' ? 'block' : 'none' }}>
            {visitedTabs.includes('alerts') && (
              <AlertsTab 
                anomalies={anomalies} setAnomalies={setAnomalies} 
                setGlobalData={setData}
                setGlobalLat={setLat}
                setGlobalLng={setLng}
                setGlobalEventType={setEventType}
                setActiveAnalysisSource={setActiveAnalysisSource}
                handleTabChange={handleTabChange}
              />
            )}
          </div>

        </div>
      </div>
    </div>
  )
}

export default function AppWrapper() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
