import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, MetricBox } from './ui/components';
import { Route } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Tooltip as LeafletTooltip, useMap, ZoomControl, Rectangle, Polygon } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import { BENGALURU_BOUNDARY_COORDS } from '../utils/bengaluruBoundary';
import MapLegend from './MapLegend';

const createTransitIcon = (fillColor) => L.divIcon({
  html: `<span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:${fillColor};box-shadow:0 0 10px ${fillColor};border:2px solid rgba(255,255,255,0.85);"></span>`,
  className: ''
});

const LINE_COLORS = {
  Purple: '#800080',
  Green: '#00b050',
  Yellow: '#ffd700',
  Pink: '#ff69b4'
};

const DEFAULT_TRANSIT_COLORS = {
  metro: '#800080',
  bus: '#00d2ff',
  parking: '#ffffff'
};

const getTransitIcon = (poi) => {
  if (poi.type === 'metro') {
    return createTransitIcon(LINE_COLORS[poi.line] || DEFAULT_TRANSIT_COLORS.metro);
  }
  return createTransitIcon(DEFAULT_TRANSIT_COLORS[poi.type] || '#999999');
};

// Restrict panning and zooming out to Bengaluru metropolitan area
const BENGALURU_BOUNDS = [
  [12.6, 77.3], // SouthWest corner
  [13.3, 77.8]  // NorthEast corner
];

const HeatmapLayer = ({ points }) => {
  const map = useMap();
  const [zoom, setZoom] = useState(map.getZoom());

  useEffect(() => {
    const onZoom = () => setZoom(map.getZoom());
    map.on('zoomend', onZoom);
    return () => map.off('zoomend', onZoom);
  }, [map]);

  useEffect(() => {
    if (!points || points.length === 0) return;

    const heatData = points.map(p => [p.lat, p.lng, Math.min(p.density * 45.0, 1.0)]);
    const radius = Math.min(44, Math.max(12, Math.round(12 * Math.pow(1.14, zoom - 12))));
    const blur = Math.round(radius * 0.65);

    const layer = L.heatLayer(heatData, {
      radius,
      blur,
      maxZoom: 18,
      minOpacity: 0.18,
      gradient: { 0.15: '#00d2ff', 0.45: '#ffbb00', 0.75: '#ff4b2b', 1.0: '#ff0000' }
    });

    layer.addTo(map);
    return () => {
      map.removeLayer(layer);
    };
  }, [points, map, zoom]);

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

      <div className="space-y-4">
        <div className="bg-[#111] border border-white/10 rounded-2xl p-4 shadow-xl">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-400 mb-1">Dispersal timeline</p>
              <p className="text-lg font-black text-white">{timeMin} minutes after event ends</p>
            </div>
            <div className="w-full max-w-2xl">
              <input
                type="range"
                min="0"
                max="60"
                step="5"
                value={timeMin}
                onChange={(e) => setTimeMin(parseInt(e.target.value, 10))}
                className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer accent-[#f7b731]"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <span>Event End</span>
                <span>1 Hour Later</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-6 h-[500px]">
          <div className="flex-1 rounded-2xl overflow-hidden border border-white/10 shadow-2xl relative z-0">
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
                <Marker key={i} position={[poi.lat, poi.lng]} icon={getTransitIcon(poi)}>
                  <LeafletTooltip>{poi.name} - {poi.type}{poi.line ? ` (${poi.line} Line)` : ''}</LeafletTooltip>
                </Marker>
              ))}

              {/* Bengaluru Boundary */}
              <Polygon 
                positions={BENGALURU_BOUNDARY_COORDS} 
                pathOptions={{ color: '#00d2ff', weight: 2, opacity: 0.7, dashArray: '5, 5', fill: false }}
              >
                <LeafletTooltip>Bengaluru City Boundary</LeafletTooltip>
              </Polygon>

              <HeatmapLayer points={currentSnapshot.points} />
            </MapContainer>
            <div className="px-4 pb-4">
              <MapLegend
                items={[
                  { icon: <span className="inline-block w-4 h-4 rounded-full bg-[#800080]" />, label: 'Purple Line Metro', description: 'Purple-line metro stations' },
                  { icon: <span className="inline-block w-4 h-4 rounded-full bg-[#00b050]" />, label: 'Green Line Metro', description: 'Green-line metro stations' },
                  { icon: <span className="inline-block w-4 h-4 rounded-full bg-[#ffd700]" />, label: 'Yellow Line Metro', description: 'Yellow-line metro stations' },
                  { icon: <span className="inline-block w-4 h-4 rounded-full bg-[#ff69b4]" />, label: 'Pink Line Metro', description: 'Pink-line metro stations' },
                  { icon: <span className="inline-block w-4 h-4 rounded-full bg-[#00d2ff]" />, label: 'Bus Stop', description: 'BMTC bus stop locations' },
                  { icon: <span className="inline-block w-4 h-4 rounded-full bg-white border border-white/20" />, label: 'Parking', description: 'Parking hub locations' },
                  { icon: <span className="inline-block w-14 h-2 rounded-full bg-[#00d2ff]" />, label: 'Bengaluru Boundary', description: 'Administrative city boundary' },
                  { icon: <span className="inline-block w-14 h-2 rounded-full bg-[#ff4b2b]" />, label: 'Heatmap', description: 'Crowd intensity and dispersal zones' }
                ]}
              />
            </div>
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
    </div>
  );
};
