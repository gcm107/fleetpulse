import React from 'react';
import { Wind, Eye, Thermometer, Gauge, CloudRain, Clock, Cloud } from 'lucide-react';
import Badge from '../common/Badge';

const CATEGORY_STYLES = {
  VFR: { variant: 'success', label: 'VFR' },
  MVFR: { variant: 'info', label: 'MVFR' },
  IFR: { variant: 'danger', label: 'IFR' },
  LIFR: { color: 'bg-pink-500/15 text-pink-400 border-pink-500/30', label: 'LIFR' },
};

function FlightCategoryBadge({ category }) {
  if (!category) return null;
  const upper = category.toUpperCase();
  const style = CATEGORY_STYLES[upper];
  if (upper === 'LIFR') {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xxs font-semibold uppercase tracking-wider border ${style.color}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-pink-400" />
        {style.label}
      </span>
    );
  }
  if (style) return <Badge variant={style.variant} dot>{style.label}</Badge>;
  return <Badge variant="neutral">{category}</Badge>;
}

function WeatherField({ icon: Icon, label, value, mono = false }) {
  return (
    <div className="flex items-start gap-2">
      {Icon && <Icon className="w-3.5 h-3.5 text-gray-500 mt-0.5 shrink-0" />}
      <div>
        <p className="text-xxs font-semibold uppercase tracking-wider text-gray-500">{label}</p>
        <p className={`text-sm ${mono ? 'font-mono text-blue-400' : 'text-gray-200'}`}>
          {value || '--'}
        </p>
      </div>
    </div>
  );
}

function decodeWindDir(deg) {
  if (deg == null || deg === 0) return 'Variable';
  const dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  return dirs[Math.round(deg / 22.5) % 16];
}

function formatWind(dir, spd, gust) {
  if (spd == null) return null;
  const dirStr = dir != null ? `${decodeWindDir(dir)} (${dir}\u00B0)` : 'Variable';
  let result = `${dirStr} at ${spd} kts`;
  if (gust) result += ` gusting ${gust} kts`;
  return result;
}

function decodeTafForecast(raw) {
  if (!raw) return [];
  // Split TAF into forecast groups by FM, TEMPO, BECMG, PROB
  const groups = [];
  const lines = raw.replace(/\s+/g, ' ').trim();

  // Extract the main forecast and change groups
  const parts = lines.split(/\s+(FM\d{6}|TEMPO\s|BECMG\s|PROB\d{2}\s)/);

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim();
    if (!part) continue;

    let type = 'Base';
    let text = part;

    if (part.match(/^FM\d{6}/)) {
      type = 'From';
      text = part + ' ' + (parts[i + 1] || '');
      i++;
    } else if (part.startsWith('TEMPO')) {
      type = 'Temporary';
      text = part + ' ' + (parts[i + 1] || '');
      i++;
    } else if (part.startsWith('BECMG')) {
      type = 'Becoming';
      text = part + ' ' + (parts[i + 1] || '');
      i++;
    }

    groups.push({ type, text: text.trim() });
  }

  return groups.length > 0 ? groups : [{ type: 'Full', text: raw }];
}

export default function AirportWeather({ metar, taf }) {
  if (!metar && !taf) {
    return (
      <div className="text-sm text-gray-500 text-center py-6">
        No weather data available for this station.
      </div>
    );
  }

  // Handle both field naming conventions from the API
  const m = metar || {};
  const windDir = m.wind_direction_deg ?? m.wind_direction ?? m.wdir;
  const windSpd = m.wind_speed_kts ?? m.wind_speed ?? m.wspd;
  const windGust = m.wind_gust_kts ?? m.wind_gust ?? m.wgst;
  const vis = m.visibility_sm ?? m.visibility ?? m.visib;
  const temp = m.temperature_c ?? m.temperature ?? m.temp;
  const dewp = m.dewpoint_c ?? m.dewpoint ?? m.dewp;
  const alt = m.altimeter_inhg ?? m.altimeter ?? m.altim;
  const ceil = m.ceiling_ft ?? m.ceiling;
  const cat = m.flight_category ?? m.fltcat ?? m.fltCat;
  const rawMetar = m.raw_text ?? m.raw ?? m.rawOb;
  const obsTime = m.observation_time ?? m.time ?? m.reportTime;

  const t = taf || {};
  const rawTaf = t.raw_text ?? t.raw ?? t.rawTAF;

  return (
    <div className="space-y-4">
      {/* METAR */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            METAR
          </h4>
          {metar && <FlightCategoryBadge category={cat} />}
        </div>

        {metar && rawMetar ? (
          <>
            <div className="bg-zinc-900/50 border border-zinc-800/30 rounded-lg p-3 mb-3">
              <p className="text-xs font-mono text-gray-300 leading-relaxed break-all">
                {rawMetar}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <WeatherField icon={Wind} label="Wind" value={formatWind(windDir, windSpd, windGust)} mono />
              <WeatherField icon={Eye} label="Visibility" value={vis != null ? `${vis} SM` : null} mono />
              <WeatherField icon={CloudRain} label="Ceiling" value={ceil != null ? `${Number(ceil).toLocaleString()} ft` : 'Clear'} mono />
              <WeatherField icon={Thermometer} label="Temp / Dewpoint" value={temp != null ? `${temp}\u00B0C / ${dewp ?? '--'}\u00B0C` : null} mono />
              <WeatherField icon={Gauge} label="Altimeter" value={alt != null ? `${Number(alt).toFixed(2)} inHg` : null} mono />
              <WeatherField icon={Clock} label="Observation" value={obsTime ? String(obsTime).replace('T', ' ').replace('Z', ' UTC').substring(0, 20) : null} mono />
            </div>
          </>
        ) : (
          <p className="text-xs text-gray-600">No METAR observations available for this station.</p>
        )}
      </div>

      {/* TAF */}
      <div className="border-t border-zinc-800/50 pt-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
          TAF (Terminal Aerodrome Forecast)
        </h4>

        {rawTaf ? (
          <>
            <div className="bg-zinc-900/50 border border-zinc-800/30 rounded-lg p-3 mb-3">
              <p className="text-xs font-mono text-gray-300 leading-relaxed break-all">
                {rawTaf}
              </p>
            </div>
            {t.valid_from && t.valid_to && (
              <p className="text-xxs text-gray-500 mb-3">
                Valid: {String(t.valid_from).replace('T', ' ').substring(0, 16)} to {String(t.valid_to).replace('T', ' ').substring(0, 16)} UTC
              </p>
            )}
            {/* Decoded TAF groups */}
            <div className="space-y-2">
              {decodeTafForecast(rawTaf).map((group, i) => (
                <div key={i} className="bg-zinc-800/30 rounded-lg px-3 py-2 border border-zinc-800/20">
                  <div className="flex items-center gap-2 mb-1">
                    <Cloud className="w-3 h-3 text-gray-500" />
                    <span className="text-xxs font-semibold uppercase tracking-wider text-gray-500">
                      {group.type}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-gray-400">{group.text}</p>
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="text-xs text-gray-600">No TAF forecast available for this station.</p>
        )}
      </div>
    </div>
  );
}
