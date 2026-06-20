import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, MetricBox } from './ui/components';
import { Route, Info } from 'lucide-react';
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
      <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 border-b border-[var(--color-border)] pb-4">
        <Route className="text-[var(--color-accent)]" size={28}/> Crowd Dispersal Simulation
      </h2>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <MetricBox title="Near Venue (<500m)" value={`${Math.round(currentSnapshot.remaining_pct)}%`} />
        <MetricBox title="Est. Clearance" value={`${clearanceMin} min`} />
        <MetricBox title="Metro Stations" value={metro_ct} subtitle="STATIONS" />
        <MetricBox title="Bus + Parking" value={bus_ct + park_ct} subtitle="HUBS" />
      </div>

      <div className="space-y-4">
        <div className="bg-[var(--color-surface)] rounded-xl p-4 shadow-2xl">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-[var(--color-accent)] mb-1 font-bold">Dispersal timeline</p>
              <p className="text-lg font-bold text-[var(--color-text-main)]">{timeMin} minutes after event ends</p>
            </div>
            <div className="w-full max-w-2xl">
              <input
                type="range"
                min="0"
                max={snapshots[snapshots.length - 1].time_min}
                step="5"
                value={timeMin}
                onChange={(e) => setTimeMin(parseInt(e.target.value, 10))}
                style={{ accentColor: 'var(--color-accent)' }}
                className="w-full h-2 bg-[var(--color-base)] rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[var(--color-text-muted)] mt-2">
                <span>Event End</span>
                <span>{snapshots[snapshots.length - 1].time_min / 60} Hours Later</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-6 h-[500px]">
          <div className="flex-1 rounded-xl overflow-hidden shadow-2xl relative z-0">
            <MapContainer 
              center={[lat, lng]} 
              zoom={14} 
              style={{ height: '100%', width: '100%', backgroundColor: 'var(--color-base)' }}
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
                pathOptions={{ color: 'var(--color-accent)', weight: 2, opacity: 0.7, dashArray: '5, 5', fill: false }}
              >
                <LeafletTooltip>Bengaluru City Boundary</LeafletTooltip>
              </Polygon>

              <HeatmapLayer points={currentSnapshot.points} />
            </MapContainer>
          </div>

          <div className="w-[320px] flex flex-col gap-3 pb-2">
            <Card className="relative overflow-visible !p-3">
              <div className="absolute top-1 right-1 group z-50">
                <button
                  type="button"
                  className="flex items-center justify-center p-2 text-[var(--color-accent)] transition duration-200 hover:scale-110"
                >
                  <Info size={16} />
                </button>
                <div className="pointer-events-none absolute right-0 top-0 -translate-y-full z-50 hidden w-80 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-sm text-[var(--color-text-main)] shadow-xl group-hover:block">
                  <strong className="block mb-2 text-[var(--color-text-main)]">Economic Segment Calculation</strong>
                  <p className="leading-6 text-[var(--color-text-muted)]">
                    This score combines the predicted crowd dispersal model with local economic sensitivity. It weighs the expected proportion of premium, middle and mass segments against the likely revenue impact from nearby venues, transportation mode shifts, and disruption penalties.
                  </p>
                </div>
              </div>
              <p className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Economic Segment</p>
              <div className="flex justify-start items-center gap-3 mb-2">
                <h3 className="text-xl font-bold text-[var(--color-text-main)]">{eco_profile.segment}</h3>
                <div className="bg-[var(--color-accent)] text-[#050505] w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm">
                  {Math.round(eco_profile.score * 100)}
                </div>
              </div>
              <div className="text-xs space-y-1 mb-2 text-[var(--color-text-main)]">
                <div className="flex justify-between"><span>Premium:</span> <b>{eco_profile.rich_pct}%</b></div>
                <div className="flex justify-between"><span>Middle:</span> <b>{eco_profile.middle_pct}%</b></div>
                <div className="flex justify-between"><span>Mass:</span> <b>{eco_profile.lower_pct}%</b></div>
              </div>
              <div className="text-xs bg-[var(--color-base)] text-[var(--color-text-main)] p-2 rounded">
                Primary Mode: <b className="text-[var(--color-accent)]">{eco_profile.primary_mode}</b>
              </div>
            </Card>

            <Card className="!p-3">
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2">Expected Mode Split</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[var(--color-text-main)] font-bold">Metro</span>
                  <span className="text-[var(--color-accent)]">{eco_profile.transport_split.metro_pct}%</span>
                </div>
                <div className="w-full bg-[var(--color-base)] h-2 rounded overflow-hidden">
                  <div className="bg-[var(--color-accent)] h-full" style={{width: `${eco_profile.transport_split.metro_pct}%`}}></div>
                </div>

                <div className="flex justify-between items-center text-sm mt-2">
                  <span className="text-[var(--color-text-main)] font-bold">Cab/Auto</span>
                  <span className="text-[var(--color-accent)]">{eco_profile.transport_split.cab_pct}%</span>
                </div>
                <div className="w-full bg-[var(--color-base)] h-2 rounded overflow-hidden">
                  <div className="bg-[var(--color-accent)] h-full opacity-70" style={{width: `${eco_profile.transport_split.cab_pct}%`}}></div>
                </div>
              </div>
            </Card>

            <MapLegend
              items={[
                { icon: <span className="inline-block w-[14px] h-[14px] rounded-full border-2 border-white/80" style={{ background: '#800080', boxShadow: '0 0 8px #800080' }} />, label: 'Metro' },
                { icon: <span className="inline-block w-[14px] h-[14px] rounded-full border-2 border-white/80" style={{ background: '#00d2ff', boxShadow: '0 0 8px #00d2ff' }} />, label: 'Bus' },
                { icon: <span className="inline-block w-[14px] h-[14px] rounded-full border-2 border-white/80" style={{ background: '#ffffff', boxShadow: '0 0 8px #ffffff' }} />, label: 'Parking' }
              ]}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
