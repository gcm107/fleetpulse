import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const DARK_TILES = 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const DARK_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>';

function createPlaneIcon(heading = 0) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" style="transform: rotate(${heading}deg);">
    <path d="M12 2 L14 8 L20 10 L14 12 L14 18 L17 20 L17 21 L12 19 L7 21 L7 20 L10 18 L10 12 L4 10 L10 8 Z"
      fill="#3b82f6" stroke="#09090b" stroke-width="0.8"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: 'plane-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

function formatValue(val, unit = '') {
  if (val == null || val === '') return '--';
  return `${val}${unit}`;
}

export default function FlightMap({ positions = [] }) {
  const markers = useMemo(
    () =>
      positions
        .filter((p) => p.latitude != null && p.longitude != null)
        .map((p, i) => ({
          key: p.transponder_hex || p.n_number || `pos-${i}`,
          position: [p.latitude, p.longitude],
          icon: createPlaneIcon(p.track_deg || 0),
          data: p,
        })),
    [positions]
  );

  return (
    <div className="w-full h-full min-h-[400px] rounded-lg overflow-hidden border border-zinc-800/50">
      <style>{`
        .plane-marker { background: transparent !important; border: none !important; }
        .leaflet-popup-content-wrapper {
          background: #1c1c1e !important;
          border: 1px solid rgba(59, 130, 246, 0.3) !important;
          border-radius: 0.5rem !important;
          color: #e5e7eb !important;
        }
        .leaflet-popup-tip { background: #1c1c1e !important; }
        .leaflet-popup-close-button { color: #9ca3af !important; }
        .leaflet-control-zoom a {
          background: #27272a !important;
          color: #e5e7eb !important;
          border-color: #3f3f46 !important;
        }
        .leaflet-control-zoom a:hover { background: #3f3f46 !important; }
        .leaflet-control-attribution {
          background: rgba(9, 9, 11, 0.8) !important;
          color: #6b7280 !important;
        }
        .leaflet-control-attribution a { color: #3b82f6 !important; }
      `}</style>
      <MapContainer
        center={[39, -98]}
        zoom={4}
        style={{ width: '100%', height: '100%', minHeight: '400px', background: '#09090b' }}
        zoomControl={true}
      >
        <TileLayer url={DARK_TILES} attribution={DARK_ATTRIBUTION} />
        {markers.map((m) => (
          <Marker key={m.key} position={m.position} icon={m.icon}>
            <Popup>
              <div className="text-sm space-y-1.5 min-w-[180px]">
                {m.data.callsign && (
                  <div className="font-bold text-blue-400 text-base tracking-wide">
                    {m.data.callsign}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                  <span className="text-gray-400">N-Number</span>
                  <span className="font-mono text-gray-200">
                    {m.data.n_number ? `N${m.data.n_number}` : '--'}
                  </span>
                  <span className="text-gray-400">Hex</span>
                  <span className="font-mono text-gray-200">
                    {formatValue(m.data.transponder_hex)}
                  </span>
                  <span className="text-gray-400">Altitude</span>
                  <span className="font-mono text-gray-200">
                    {formatValue(m.data.altitude_ft, ' ft')}
                  </span>
                  <span className="text-gray-400">Speed</span>
                  <span className="font-mono text-gray-200">
                    {formatValue(m.data.ground_speed_kts, ' kts')}
                  </span>
                  <span className="text-gray-400">Heading</span>
                  <span className="font-mono text-gray-200">
                    {formatValue(m.data.track_deg, '\u00B0')}
                  </span>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
