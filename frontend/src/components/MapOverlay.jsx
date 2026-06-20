import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Polyline, Polygon, Tooltip as LeafletTooltip, useMapEvents, useMap, ZoomControl, GeoJSON, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import { BENGALURU_BOUNDARY_COORDS } from '../utils/bengaluruBoundary';

const venueIcon = new L.divIcon({
  className: 'custom-venue-icon',
  html: `<svg viewBox="0 0 24 24" width="36" height="36" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.5));">
           <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="var(--color-accent)"/>
         </svg>`,
  iconSize: [36, 36],
  iconAnchor: [18, 36],
  popupAnchor: [0, -36]
});

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

function DynamicRoads({ roads, overlayVisibility, roadZoom, setRoadZoom }) {
  const map = useMap();

  useEffect(() => {
    setRoadZoom(map.getZoom());
    const onZoom = () => setRoadZoom(map.getZoom());
    map.on('zoomend', onZoom);
    return () => map.off('zoomend', onZoom);
  }, [map, setRoadZoom]);

  return (
    <>
      {roads?.map((road, idx) => {
        const visible = overlayVisibility ? (overlayVisibility[`risk-${idx}`] ?? true) : true;
        if (!visible) return null;
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

// Controller component inside MapContainer to receive map instance
function OverlayController({ overlayItemsRef }) {
  const map = useMap();
  useEffect(() => {
    const handler = (e) => {
      const { id } = e.detail || {};
      if (!id) return;
      const items = overlayItemsRef.current || [];
      const item = items.find(it => it.id === id);
      if (!item || !item.positions || item.positions.length === 0) return;
      // compute bounds
      const lats = item.positions.map(p => p[0]);
      const lngs = item.positions.map(p => p[1]);
      const south = Math.min(...lats);
      const north = Math.max(...lats);
      const west = Math.min(...lngs);
      const east = Math.max(...lngs);
      try {
        map.fitBounds([[south, west], [north, east]], { padding: [40, 40] });
      } catch (err) {
        console.error('Overlay focus error', err);
      }
    };
    window.addEventListener('overlayFocus', handler);
    return () => window.removeEventListener('overlayFocus', handler);
  }, [map, overlayItemsRef]);
  return null;
}

export default function MapOverlay({ lat, lng, showPin, setLocation, locationName, setLocationName, predictionData, criticalRoads, emergencyRoutes, initialMapData, targetBoundary, setTargetBoundary }) {

  const [externalTraffic, setExternalTraffic] = React.useState(null);
  const [roadZoom, setRoadZoom] = useState(14);

  // Overlay visibility state (toggled by Legend)
  const [overlayVisibility, setOverlayVisibility] = useState({});

  const overlayItemsRef = useRef([]);

  // Emit overlay state for dynamic legend (includes positions for focus)
  useEffect(() => {
    const emit = () => {
      const items = [];
      if (showPin) items.push({ id: 'pin', label: 'Selected Pin', type: 'marker', color: 'var(--color-accent)', visible: overlayVisibility['pin'] ?? true, positions: [[lat, lng]] });

      // critical roads (high risk)
      if (criticalRoads && criticalRoads.length > 0) {
        const colors = ['#ff2a00', '#ff4b2b', '#ff8c00', '#ffb700', '#ffea00'];
        criticalRoads.forEach((r, i) => items.push({ id: `risk-${i}`, label: `High Risk Route ${i+1}`, type: 'line', color: colors[i % colors.length], dashed: false, visible: overlayVisibility[`risk-${i}`] ?? true, positions: r.coordinates || [] }));
      }

      // emergency routes
      if (emergencyRoutes && emergencyRoutes.length > 0) {
        const greenShades = ['#00e676', '#b2ff59', '#64dd17'];
        let hospIdx = 0;
        emergencyRoutes.forEach((route, i) => {
          if (route.type === 'hospital' || !route.type) {
            const color = greenShades[hospIdx % greenShades.length];
            hospIdx++;
            items.push({ id: `em-detour-${i}`, label: `Emergency Route (${route.name || i+1})`, type: 'line', color: color, visible: overlayVisibility[`em-detour-${i}`] ?? true, positions: route.detour_path || [] });
          }
        });
      }

      // external traffic (TomTom) - include positions when available
      if (externalTraffic?.flow && Array.isArray(externalTraffic.flow)) {
        const roadColors = ['#ff00ff', '#00b0ff', '#ffea00', '#ff0000', '#00ff00']; // pink, blue, yellow, red, green
        const seenCoords = new Set();
        let displayIdx = 0;
        externalTraffic.flow.forEach((rf, idx) => {
          const segment = rf.flow?.flowSegmentData;
          const coords = (segment?.coordinates?.coordinate || []).map(c => [c.latitude, c.longitude]);
          if (coords.length > 0) {
            const coordStr = coords.flat().join(',');
            if (!seenCoords.has(coordStr)) {
              seenCoords.add(coordStr);
              items.push({ id: `tt-${idx}`, label: rf.road_name || `Traffic ${idx+1}`, type: 'line', color: roadColors[displayIdx % roadColors.length], dashed: true, visible: overlayVisibility[`tt-${idx}`] ?? true, positions: coords });
              displayIdx++;
            }
          }
        });
      } else if (externalTraffic?.flow && externalTraffic.flow.flowSegmentData) {
        const speed = externalTraffic.flow.flowSegmentData?.currentSpeed || 0;
        const speedColor = speed < 10 ? '#ff4444' : speed < 20 ? '#ffaa00' : '#44ff44';
        const coordsSingle = (externalTraffic.flow.flowSegmentData.coordinates.coordinate || []).map(c => [c.latitude, c.longitude]);
        items.push({ id: 'tt-single', label: 'Traffic (TomTom)', type: 'line', color: speedColor, dashed: true, visible: overlayVisibility['tt-single'] ?? true, positions: coordsSingle });
      }

      overlayItemsRef.current = items;
      window.dispatchEvent(new CustomEvent('overlayStateUpdate', { detail: { items } }));
    };

    emit();
  }, [externalTraffic, criticalRoads, emergencyRoutes, showPin, overlayVisibility, lat, lng]);

  // Listen for visibility changes from Legend
  useEffect(() => {
    const handler = (e) => {
      const { id, visible } = e.detail || {};
      if (!id) return;
      setOverlayVisibility((prev) => ({ ...prev, [id]: visible }));
    };
    window.addEventListener('overlayVisibilityChange', handler);
    // respond to requests for current overlay state
    const reqHandler = () => {
      window.dispatchEvent(new CustomEvent('overlayStateUpdate', { detail: { items: overlayItemsRef.current || [] } }));
    };
    window.addEventListener('requestOverlayState', reqHandler);
    return () => window.removeEventListener('overlayVisibilityChange', handler);
  }, []);

  // Listen for external traffic payloads (dispatched by LiveDashboard)
  useEffect(() => {
    const handler = (e) => {
      setExternalTraffic(e.detail || null);
    };
    window.addEventListener('externalTraffic', handler);
    return () => window.removeEventListener('externalTraffic', handler);
  }, []);

  const corridors = initialMapData?.metro_corridors || [];

  const renderCommonElements = () => (
    <>
      {setLocation && <MapClickHandler setLocation={setLocation} setLocationName={setLocationName} setTargetBoundary={setTargetBoundary} />}

      {showPin && (overlayVisibility['pin'] ?? true) && (
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



  // Active prediction state
  const radius = predictionData.total_incidents * 15;

  return (
    <MapContainer
      center={[lat, lng]}
      zoom={14}
      style={{ height: '100%', width: '100%', backgroundColor: '#111' }}
      zoomControl={false}
      maxBounds={BENGALURU_BOUNDS}
      minZoom={10}
    >
      {/* Controller to handle focus events using the map instance */}
      <OverlayController overlayItemsRef={overlayItemsRef} />
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

      <DynamicRoads roads={criticalRoads} overlayVisibility={overlayVisibility} roadZoom={roadZoom} setRoadZoom={setRoadZoom} />

      {(() => {
        let hospIdx = 0;
        const greenShades = ['#00e676', '#b2ff59', '#64dd17'];
        return emergencyRoutes?.map((route, idx) => {
          if (route.type && route.type !== 'hospital') return null;
          
          const destination = route.detour_path && route.detour_path.length > 0 ? route.detour_path[route.detour_path.length - 1] : null;
          const showDetour = overlayVisibility ? (overlayVisibility[`em-detour-${idx}`] ?? true) : true;
          const color = greenShades[hospIdx % greenShades.length];
          hospIdx++;

          return (
            <React.Fragment key={`emergency-${idx}`}>
              {showDetour && (
                <Polyline
                  positions={route.detour_path}
                  pathOptions={{ color: color, weight: 3.5, opacity: 0.9 }}
                >
                  <LeafletTooltip>Emergency Route ({route.name})</LeafletTooltip>
                </Polyline>
              )}
            {destination && (
              <CircleMarker 
                center={destination} 
                radius={6}
                pathOptions={{ color: '#111', fillColor: color, fillOpacity: 1, weight: 2 }}
              >
                <LeafletTooltip direction="top" permanent={false} opacity={1} className="font-bold">
                  🏥 {route.name}
                </LeafletTooltip>
              </CircleMarker>
            )}
          </React.Fragment>
        );
      });
      })()}

      {/* Render external traffic from TomTom */}
      {externalTraffic?.flow && Array.isArray(externalTraffic.flow) ? (
        (() => {
          const roadColors = ['#ff00ff', '#00b0ff', '#ffea00', '#ff0000', '#00ff00']; // pink, blue, yellow, red, green
          const seenCoords = new Set();
          let displayIdx = 0;
          return externalTraffic.flow.map((roadFlow, roadIndex) => {
            const flow = roadFlow?.flow;
            const segment = flow?.flowSegmentData;
            const coords = (segment?.coordinates?.coordinate || []);
            const speed = segment?.currentSpeed || 0;
            
            if (coords.length === 0) return null;
            
            const positions = coords.map(c => [c.latitude, c.longitude]);
            const coordStr = positions.flat().join(',');
            if (seenCoords.has(coordStr)) return null;
            seenCoords.add(coordStr);
            
            const lineColor = roadColors[displayIdx % roadColors.length];
            const id = `tt-${roadIndex}`;
            const visible = overlayVisibility ? (overlayVisibility[id] ?? true) : true;
            displayIdx++;

            if (!visible) return null;

            return (
              <Polyline
                key={`tomtom-road-${roadIndex}`}
                positions={positions}
                pathOptions={{ color: lineColor, weight: 3, opacity: 0.95, dashArray: '8, 8' }}
              >
                <LeafletTooltip>
                  {roadFlow.road_name}: Speed {speed} km/h | Flow: {segment?.frc || 'N/A'}
                </LeafletTooltip>
              </Polyline>
            );
          });
        })()
      ) : externalTraffic?.flow?.flowSegmentData?.coordinates?.coordinate ? (
        (() => {
          const coords = externalTraffic.flow.flowSegmentData.coordinates.coordinate || [];
          if (coords.length === 0) return null;
          const speed = externalTraffic.flow.flowSegmentData?.currentSpeed || 0;
          const speedColor = speed < 10 ? '#ff4444' : speed < 20 ? '#ffaa00' : '#44ff44';
          const positions = coords.map(c => [c.latitude, c.longitude]);
          const visible = overlayVisibility ? (overlayVisibility['tt-single'] ?? true) : true;
          if (!visible) return null;
          return (
            <Polyline
              key={`tomtom-single`}
              positions={positions}
              pathOptions={{ color: speedColor, weight: 3, opacity: 0.95, dashArray: '8, 8' }}
            >
              <LeafletTooltip>
                Speed: {speed} km/h | Flow: {externalTraffic.flow.flowSegmentData?.frc || 'N/A'}
              </LeafletTooltip>
            </Polyline>
          );
        })()
      ) : null}

      <Polygon
        positions={BENGALURU_BOUNDARY_COORDS}
        pathOptions={{ color: '#1a4d66', weight: 1.5, opacity: 0.4, dashArray: '5, 5', fill: false }}
      >
        <LeafletTooltip>Bengaluru Boundary</LeafletTooltip>
      </Polygon>
    </MapContainer>
  );
}
