import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const DARK_TILES = 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const DARK_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>';

// Fix default marker icon for Leaflet with bundlers
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export default function AirportMap({ latitude, longitude, name, icao_code }) {
  if (latitude == null || longitude == null) return null;

  return (
    <div className="w-full rounded-lg overflow-hidden border border-zinc-800/50" style={{ height: 300 }}>
      <style>{`
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
        center={[latitude, longitude]}
        zoom={13}
        style={{ width: '100%', height: '100%', background: '#09090b' }}
        zoomControl={true}
      >
        <TileLayer url={DARK_TILES} attribution={DARK_ATTRIBUTION} />
        <Marker position={[latitude, longitude]} icon={defaultIcon}>
          <Popup>
            <div className="text-sm space-y-1 min-w-[140px]">
              <div className="font-bold text-blue-400">{name || 'Airport'}</div>
              {icao_code && (
                <div className="text-xs text-gray-400">
                  ICAO: <span className="font-mono text-gray-200">{icao_code}</span>
                </div>
              )}
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
