import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, MetricBox } from './ui/components';
import { Route } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Tooltip as LeafletTooltip, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

const transitIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
  popupAnchor: [1, -28],
  shadowSize: [32, 32]
});

// Restrict panning and zooming out to Bengaluru metropolitan area
const BENGALURU_BOUNDS = [
  [12.6, 77.3], // SouthWest corner
  [13.3, 77.8]  // NorthEast corner
];

const HeatmapLayer = ({ points }) => {
  const map = useMap();
  
  useEffect(() => {
    if (!points || points.length === 0) return;
    
    // Format: [lat, lng, intensity]
    const heatData = points.map(p => [p.lat, p.lng, Math.min(p.density * 30.0, 1.0)]);
    
    const layer = L.heatLayer(heatData, {
      radius: 35,
      blur: 25,
      maxZoom: 18,
      minOpacity: 0.45,
      gradient: { 0.1: "#00d2ff", 0.4: "#ffbb00", 0.7: "#ff4b2b", 1.0: "#ff0000" }
    });
    
    layer.addTo(map);
    
    return () => {
      map.removeLayer(layer);
    };
  }, [points, map]);

  return null;
};

export const DispersalTab = ({ lat, lng, eventType, totalIncidents }) => {
  const [timeMin, setTimeMin] = useState(15);
  const [dispersalData, setDispersalData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDispersal = async () => {
      setLoading(true);
      try {
        const res = await axios.post('http://localhost:8000/api/dispersal', {
          event_type: eventType,
          latitude: lat,
          longitude: lng,
          total_incidents: totalIncidents,
          crowd_size: totalIncidents * 150
        });
        setDispersalData(res.data);
      } catch (err) {
        console.error("Dispersal fetch error:", err);
      }
      setLoading(false);
    };
    
    if (lat && lng) fetchDispersal();
  }, [lat, lng, eventType, totalIncidents]);

  if (loading || !dispersalData) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Generating high-fidelity crowd simulation...
      </div>
    );
  }

  const { eco_profile, transit_pois, snapshots } = dispersalData;
  const currentSnapshot = snapshots.find(s => s.time_min === timeMin) || snapshots[0];
  
  let clearanceMin = 60;
  for (const s of snapshots) {
    if (s.remaining_pct < 10) {
      clearanceMin = s.time_min;
      break;
    }
  }

  const metro_ct = transit_pois.filter(p => p.type === 'metro').length;
  const bus_ct = transit_pois.filter(p => p.type === 'bus').length;
  const park_ct = transit_pois.filter(p => p.type === 'parking').length;

  return (
    <div className="flex-1 max-w-6xl mx-auto space-y-6 w-full">
      <h2 className="text-2xl font-black mb-2 flex items-center gap-2 border-b border-white/10 pb-4">
        <Route className="text-[#f7b731]" size={28}/> Crowd Dispersal Simulation
      </h2>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <MetricBox title="Near Venue (<500m)" value={`${Math.round(currentSnapshot.remaining_pct)}%`} colorClass="text-[#00d2ff]" />
        <MetricBox title="Est. Clearance" value={`${clearanceMin} min`} colorClass="text-[#00e676]" />
        <MetricBox title="Metro Stations" value={metro_ct} colorClass="text-[#c77dff]" subtitle="STATIONS" />
        <MetricBox title="Bus + Parking" value={bus_ct + park_ct} colorClass="text-yellow-500" subtitle="HUBS" />
      </div>

      <div className="flex gap-6 h-[500px]">
        <div className="flex-1 rounded-2xl overflow-hidden border border-white/10 shadow-2xl relative z-0">
          <div className="absolute top-4 left-4 right-4 z-[400] bg-black/60 backdrop-blur-md p-4 rounded-lg border border-white/10">
            <label className="block text-sm font-bold text-white mb-2">
              Time after event ends: <span className="text-[#f7b731]">{timeMin} minutes</span>
            </label>
            <input 
              type="range" min="0" max="60" step="5" value={timeMin}
              onChange={(e) => setTimeMin(parseInt(e.target.value))}
              className="w-full accent-[#f7b731]"
            />
          </div>
          <MapContainer 
            center={[lat, lng]} 
            zoom={14} 
            style={{ height: '100%', width: '100%', backgroundColor: '#111' }}
            zoomControl={false}
            maxBounds={BENGALURU_BOUNDS}
            minZoom={10}
          >
            <ZoomControl position="bottomright" />
            <TileLayer url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png" />
            
            {transit_pois.map((poi, i) => (
              <Marker key={i} position={[poi.lat, poi.lng]} icon={transitIcon}>
                <LeafletTooltip>{poi.name} - {poi.type}</LeafletTooltip>
              </Marker>
            ))}

            {/* True Canvas Heatmap */}
            <HeatmapLayer points={currentSnapshot.points} />
          </MapContainer>
        </div>

        <div className="w-[320px] flex flex-col gap-4">
          <Card className="bg-gradient-to-br from-[#00d2ff]/10 to-[#3a7bd5]/5 border-[#00d2ff]/30">
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Economic Segment</p>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-2xl font-black">{eco_profile.segment}</h3>
              <div className="bg-[#00d2ff] text-black w-12 h-12 rounded-full flex items-center justify-center font-black text-xl">
                {Math.round(eco_profile.score * 100)}
              </div>
            </div>
            <div className="text-sm space-y-1 mb-4">
              <div>Premium: <b>{eco_profile.rich_pct}%</b></div>
              <div>Middle: <b>{eco_profile.middle_pct}%</b></div>
              <div>Mass: <b>{eco_profile.lower_pct}%</b></div>
            </div>
            <div className="text-sm bg-black/30 p-2 rounded">
              Primary Mode: <b>{eco_profile.primary_mode}</b>
            </div>
          </Card>

          <Card>
            <h3 className="text-sm font-bold text-gray-300 mb-3">Expected Mode Split</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-[#c77dff] font-bold">Metro</span>
                <span>{eco_profile.transport_split.metro_pct}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded overflow-hidden">
                <div className="bg-[#c77dff] h-full" style={{width: `${eco_profile.transport_split.metro_pct}%`}}></div>
              </div>
              
              <div className="flex justify-between items-center text-sm mt-2">
                <span className="text-yellow-500 font-bold">Cab/Auto</span>
                <span>{eco_profile.transport_split.cab_pct}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded overflow-hidden">
                <div className="bg-yellow-500 h-full" style={{width: `${eco_profile.transport_split.cab_pct}%`}}></div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
