import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Polyline, Polygon, Tooltip as LeafletTooltip, useMapEvents, useMap, ZoomControl, GeoJSON, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import { BENGALURU_BOUNDARY_COORDS } from '../utils/bengaluruBoundary';

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

function MapClickHandler({ setLocation, setLocationName, setTargetBoundary }) {
  useMapEvents({
    click: async (e) => {
      const { lat, lng } = e.latlng;
      if (setLocation) setLocation({ lat, lng });
      if (setTargetBoundary) setTargetBoundary(null);
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

function MapAutoZoom({ lat, lng, predictionData }) {
  const map = useMap();
  useEffect(() => {
    if (lat && lng) {
      // Zoom in tight to 16 to clearly see the pin and the analysis area
      map.flyTo([lat, lng], 16, { duration: 1.5 });
    }
  }, [lat, lng, predictionData, map]);
  return null;
}

// Restrict panning and zooming out to Bengaluru metropolitan area
const BENGALURU_BOUNDS = [
  [12.6, 77.3], // SouthWest corner
  [13.3, 77.8]  // NorthEast corner
];

export default function MapOverlay({ lat, lng, showPin, setLocation, locationName, setLocationName, predictionData, criticalRoads, emergencyRoutes, initialMapData, targetBoundary, setTargetBoundary }) {

  const corridors = initialMapData?.metro_corridors || [];

  const renderCommonElements = () => (
    <>
      {setLocation && <MapClickHandler setLocation={setLocation} setLocationName={setLocationName} setTargetBoundary={setTargetBoundary} />}

      {showPin && (
        <Marker position={[lat, lng]} icon={venueIcon}>
          <LeafletTooltip direction="top">{locationName || "Selected Target"}</LeafletTooltip>
        </Marker>
      )}

      {corridors.map((corridor, idx) => (
        <Polyline
          key={`corridor-${idx}`}
          positions={corridor.coordinates}
          pathOptions={{ color: corridor.color || '#c77dff', weight: 1.5, opacity: 0.7 }}
        >
          <LeafletTooltip sticky direction="top" opacity={1}>
            {corridor.name}
          </LeafletTooltip>
        </Polyline>
      ))}

      {targetBoundary && (
        <GeoJSON 
          key={JSON.stringify(targetBoundary)}
          data={targetBoundary} 
          style={{ color: '#888', weight: 2, opacity: 0.8, fillOpacity: 0.15 }}
        >
          <LeafletTooltip direction="top">Searched Location Boundary</LeafletTooltip>
        </GeoJSON>
      )}
    </>
  );

  // If no prediction data is available, render the initial clean state
  if (!predictionData) {
    return (
      <div style={{ height: '100%' }}>
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
          <MapAutoZoom lat={lat} lng={lng} predictionData={predictionData} />
          {renderCommonElements()}
          <Polygon
            positions={BENGALURU_BOUNDARY_COORDS}
            pathOptions={{ color: '#1a4d66', weight: 1.5, opacity: 0.6, dashArray: '5, 5', fill: false }}
          >
            <LeafletTooltip>Bengaluru Boundary</LeafletTooltip>
          </Polygon>
        </MapContainer>
      </div>
    );
  }

  const [roadZoom, setRoadZoom] = useState(14);

  function DynamicRoads({ roads }) {
    const map = useMap();

    useEffect(() => {
      setRoadZoom(map.getZoom());
      const onZoom = () => setRoadZoom(map.getZoom());
      map.on('zoomend', onZoom);
      return () => map.off('zoomend', onZoom);
    }, [map]);

    return (
      <>
        {roads?.map((road, idx) => {
          const baseWeight = Math.max(2, (road.weight || 1) * 1.5);
          const scaledWeight = Math.min(14, Math.max(2.5, Math.round(baseWeight * Math.pow(1.15, roadZoom - 12))));
          
          // Color based on risk level (idx 0 is highest risk)
          const colors = ['#ff2a00', '#ff4b2b', '#ff8c00', '#ffb700', '#ffea00'];
          const roadColor = colors[idx % colors.length];

          return (
            <Polyline
              key={idx}
              positions={road.coordinates}
              pathOptions={{
                color: roadColor,
                weight: scaledWeight,
                opacity: 0.9,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            >
              <LeafletTooltip>High Risk Route</LeafletTooltip>
            </Polyline>
          );
        })}
      </>
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
      <MapAutoZoom lat={lat} lng={lng} predictionData={predictionData} />
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

      <DynamicRoads roads={criticalRoads} />

      {emergencyRoutes?.map((route, idx) => {
        const destination = route.detour_path && route.detour_path.length > 0 ? route.detour_path[route.detour_path.length - 1] : null;
        return (
          <React.Fragment key={`emergency-${idx}`}>
            <Polyline
              positions={route.primary_path}
              pathOptions={{ color: '#00d2ff', weight: 4, opacity: 0.6, dashArray: '5, 10' }}
            >
              <LeafletTooltip>Primary Hospital Route (Blocked/Risk)</LeafletTooltip>
            </Polyline>
            <Polyline
              positions={route.detour_path}
              pathOptions={{ color: '#00e676', weight: 5, opacity: 0.9 }}
            >
              <LeafletTooltip>Safe Emergency Detour ({route.name})</LeafletTooltip>
            </Polyline>
            {destination && (
              <CircleMarker 
                center={destination} 
                radius={6}
                pathOptions={{ color: '#111', fillColor: '#00e676', fillOpacity: 1, weight: 2 }}
              >
                <LeafletTooltip direction="top" permanent={false} opacity={1} className="font-bold">
                  🏥 {route.name}
                </LeafletTooltip>
              </CircleMarker>
            )}
          </React.Fragment>
        );
      })}

      <Polygon
        positions={BENGALURU_BOUNDARY_COORDS}
        pathOptions={{ color: '#1a4d66', weight: 1.5, opacity: 0.4, dashArray: '5, 5', fill: false }}
      >
        <LeafletTooltip>Bengaluru Boundary</LeafletTooltip>
      </Polygon>
    </MapContainer>
  );
}
