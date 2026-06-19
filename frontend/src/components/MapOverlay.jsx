import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Polyline, Tooltip as LeafletTooltip, useMapEvents, ZoomControl, Rectangle } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

const createCustomIcon = (color) => {
  return new L.Icon({
    iconUrl: `https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

const venueIcon = createCustomIcon('blue');

function MapClickHandler({ setLocation, setLocationName }) {
  useMapEvents({
    click: async (e) => {
      const { lat, lng } = e.latlng;
      if (setLocation) setLocation({ lat, lng });
      if (setLocationName) {
        setLocationName("Geocoding...");
        try {
          const response = await axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
          if (response.data && response.data.display_name) {
            const parts = response.data.display_name.split(',');
            setLocationName(parts.slice(0, 3).join(', '));
          } else {
            setLocationName(`LAT: ${lat.toFixed(4)}, LNG: ${lng.toFixed(4)}`);
          }
        } catch (err) {
          setLocationName(`LAT: ${lat.toFixed(4)}, LNG: ${lng.toFixed(4)}`);
        }
      }
    }
  });
  return null;
}

// Restrict panning and zooming out to Bengaluru metropolitan area
const BENGALURU_BOUNDS = [
  [12.6, 77.3], // SouthWest corner
  [13.3, 77.8]  // NorthEast corner
];

export default function MapOverlay({ lat, lng, setLocation, locationName, setLocationName, predictionData, criticalRoads, initialMapData }) {
  
  const corridors = initialMapData?.metro_corridors || [];

  const renderCommonElements = () => (
    <>
      {setLocation && <MapClickHandler setLocation={setLocation} setLocationName={setLocationName} />}
      
      <Marker position={[lat, lng]} icon={venueIcon}>
        <LeafletTooltip direction="top">{locationName || "Selected Target"}</LeafletTooltip>
      </Marker>

      {corridors.map((corridor, idx) => (
        <Polyline 
          key={`corridor-${idx}`} 
          positions={corridor.coordinates} 
          pathOptions={{ color: corridor.color || '#c77dff', weight: 4, opacity: 0.8 }}
        >
          <LeafletTooltip sticky direction="top" opacity={1}>
            {corridor.name}
          </LeafletTooltip>
        </Polyline>
      ))}
    </>
  );

  // If no prediction data is available, render the initial clean state
  if (!predictionData) {
    return (
      <MapContainer 
        center={[lat, lng]} 
        zoom={12} 
        style={{ height: '100%', width: '100%', backgroundColor: '#111' }}
        className="z-0"
        zoomControl={false}
        maxBounds={BENGALURU_BOUNDS}
        minZoom={10}
      >
        <ZoomControl position="bottomright" />
        <TileLayer
          url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png"
          attribution='&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
        />
        {renderCommonElements()}
      </MapContainer>
    );
  }

  // Active prediction state
  const radius = predictionData.total_incidents * 15;
  
  return (
    <MapContainer 
      center={[lat, lng]} 
      zoom={14} 
      style={{ height: '100%', width: '100%', backgroundColor: '#111' }}
      className="z-0"
      zoomControl={false}
      maxBounds={BENGALURU_BOUNDS}
      minZoom={10}
    >
      <ZoomControl position="bottomright" />
      <TileLayer
        url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png"
        attribution='&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
      />
      {renderCommonElements()}

      <Circle 
        center={[lat, lng]} 
        radius={radius} 
        pathOptions={{ color: '#ff4b2b', fillColor: '#ff4b2b', fillOpacity: 0.1, weight: 2 }}
      >
        <LeafletTooltip>Impact Zone</LeafletTooltip>
      </Circle>

      <Circle 
        center={[lat, lng]} 
        radius={radius * 1.5} 
        pathOptions={{ color: '#00d2ff', fillColor: 'transparent', weight: 2, dashArray: '5, 10' }}
      >
        <LeafletTooltip>Spillover Zone</LeafletTooltip>
      </Circle>

      {criticalRoads && criticalRoads.map((road, idx) => (
        <Polyline 
          key={idx} 
          positions={road.coordinates} 
          pathOptions={{ color: '#ff4b2b', weight: road.weight * 2, opacity: 0.8 }}
        >
          <LeafletTooltip>High Risk Route</LeafletTooltip>
        </Polyline>
      ))}

      <Rectangle 
        bounds={BENGALURU_BOUNDS} 
        pathOptions={{ color: '#00d2ff', weight: 2, opacity: 0.5, dashArray: '5, 5', fill: false }}
      >
        <LeafletTooltip>Bengaluru Boundary</LeafletTooltip>
      </Rectangle>
    </MapContainer>
  );
}
