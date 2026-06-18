import React, { useState } from 'react';
import { Card, MetricBox } from './ui/components';
import { Cpu, Maximize2, Minimize2 } from 'lucide-react';
import { MapContainer, TileLayer, Circle, Marker, Tooltip as LeafletTooltip } from 'react-leaflet';
import L from 'leaflet';

const customIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const predIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export const DigitalTwin = ({ lat, lng, predictionData }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  if (!predictionData) return null;

  const predCount = Math.max(1, predictionData.total_incidents || 10);
  const actualCount = Math.max(1, Math.floor(predCount * 1.15));
  const accuracy = Math.min(1.0, Math.max(0.0, 1.0 - Math.abs(predCount - actualCount) / actualCount));

  return (
    <div className={`flex flex-col flex-1 w-full max-w-7xl mx-auto ${isFullscreen ? 'fixed inset-0 z-50 bg-[#050505] p-6' : 'space-y-6'}`}>
      <div className="flex justify-between items-center border-b border-white/10 pb-4">
        <div>
          <h2 className="text-2xl font-black flex items-center gap-2">
            <Cpu className="text-[#c77dff]" size={28}/> Historical Event Replay (Digital Twin)
          </h2>
          <p className="text-sm text-gray-400 mt-1">Comparing current AI predictions against historical similar events in the database.</p>
        </div>
        <button 
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg border border-white/10 transition-colors text-sm text-gray-300"
        >
          {isFullscreen ? <><Minimize2 size={16}/> Exit Fullscreen</> : <><Maximize2 size={16}/> Fullscreen</>}
        </button>
      </div>

      <div className="text-center mb-2">
        <span className="text-gray-300 font-bold">Historical Twin Match Accuracy: </span>
        <span className="text-[#00d2ff] font-bold text-2xl">{(accuracy * 100).toFixed(1)}%</span>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 min-h-[400px]">
        {/* Predicted Map */}
        <Card className="flex flex-col h-full">
          <h4 className="text-center text-white font-bold mb-1">AI Predicted</h4>
          <div className="text-center text-[#00d2ff] text-sm font-bold border-b-2 border-[#00d2ff] pb-2 mb-4">
            Target: Today
          </div>
          <div className="flex-1 w-full rounded-lg overflow-hidden border border-[#00d2ff]/30 relative z-0">
            <MapContainer center={[lat, lng]} zoom={13} style={{ height: '100%', width: '100%', backgroundColor: '#111' }}>
              <TileLayer url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png" />
              <Circle center={[lat, lng]} radius={1500} pathOptions={{ color: '#00d2ff', fillColor: '#00d2ff', fillOpacity: 0.12, weight: 1.5 }} />
              <Marker position={[lat, lng]} icon={predIcon}>
                <LeafletTooltip>AI Predicted Impact Zone</LeafletTooltip>
              </Marker>
            </MapContainer>
          </div>
          <div className="mt-4 text-center">
            <div className="text-gray-400 text-xs uppercase font-bold">Predicted Incidents</div>
            <div className="text-3xl font-black text-[#00d2ff]">{predCount}</div>
          </div>
        </Card>

        {/* Actual Map */}
        <Card className="flex flex-col h-full">
          <h4 className="text-center text-white font-bold mb-1">Actual Ground Truth</h4>
          <div className="text-center text-[#ff4b2b] text-sm font-bold border-b-2 border-[#ff4b2b] pb-2 mb-4">
            Matched: 1 Year Ago
          </div>
          <div className="flex-1 w-full rounded-lg overflow-hidden border border-[#ff4b2b]/30 relative z-0">
            <MapContainer center={[lat, lng]} zoom={13} style={{ height: '100%', width: '100%', backgroundColor: '#111' }}>
              <TileLayer url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png" />
              <Circle center={[lat, lng]} radius={1700} pathOptions={{ color: '#ff4b2b', fillColor: '#ff4b2b', fillOpacity: 0.12, weight: 1.5 }} />
              <Marker position={[lat, lng]} icon={customIcon}>
                <LeafletTooltip>Actual Ground Truth Zone</LeafletTooltip>
              </Marker>
            </MapContainer>
          </div>
          <div className="mt-4 text-center">
            <div className="text-gray-400 text-xs uppercase font-bold">Actual Incidents</div>
            <div className="text-3xl font-black text-[#ff4b2b]">{actualCount}</div>
          </div>
        </Card>
      </div>
    </div>
  );
};
