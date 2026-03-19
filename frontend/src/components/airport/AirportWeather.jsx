import React from 'react';
import { Wind, Eye, Thermometer, Gauge, CloudRain, Clock } from 'lucide-react';
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
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xxs font-semibold uppercase tracking-wider border ${style.color}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-pink-400" />
        {style.label}
      </span>
    );
  }

  if (style) {
    return (
      <Badge variant={style.variant} dot>
        {style.label}
      </Badge>
    );
  }

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

export default function AirportWeather({ metar, taf }) {
  if (!metar && !taf) {
    return (
      <div className="text-sm text-gray-500 text-center py-6">
        Weather data not available. Connect METAR/TAF feeds for live updates.
      </div>
    );
  }

  const windDisplay = metar
    ? [
        metar.wind_direction != null ? `${metar.wind_direction}\u00B0` : null,
        metar.wind_speed != null ? `${metar.wind_speed} kts` : null,
        metar.wind_gust ? `G${metar.wind_gust}` : null,
      ]
        .filter(Boolean)
        .join(' ') || '--'
    : '--';

  return (
    <div className="space-y-4">
      {/* METAR */}
      {metar && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              METAR
            </h4>
            <FlightCategoryBadge category={metar.flight_category} />
          </div>

          {/* Raw METAR */}
          {(metar.raw || metar.raw_text) && (
            <div className="bg-zinc-900/50 border border-zinc-800/30 rounded-lg p-3 mb-3">
              <p className="text-xs font-mono text-gray-300 leading-relaxed break-all">
                {metar.raw || metar.raw_text}
              </p>
            </div>
          )}

          {/* Parsed fields */}
          <div className="grid grid-cols-2 gap-3">
            <WeatherField icon={Wind} label="Wind" value={windDisplay} mono />
            <WeatherField
              icon={Eye}
              label="Visibility"
              value={metar.visibility != null ? `${metar.visibility} SM` : null}
              mono
            />
            <WeatherField
              icon={CloudRain}
              label="Ceiling"
              value={
                metar.ceiling != null
                  ? `${metar.ceiling} ft`
                  : metar.cloud_layers?.length
                  ? metar.cloud_layers
                      .map((l) => `${l.coverage} ${l.base_ft || l.altitude}ft`)
                      .join(', ')
                  : null
              }
              mono
            />
            <WeatherField
              icon={Thermometer}
              label="Temp / Dewpoint"
              value={
                metar.temperature != null
                  ? `${metar.temperature}\u00B0C / ${metar.dewpoint ?? '--'}\u00B0C`
                  : null
              }
              mono
            />
            <WeatherField
              icon={Gauge}
              label="Altimeter"
              value={metar.altimeter != null ? `${metar.altimeter} inHg` : null}
              mono
            />
            <WeatherField
              icon={Clock}
              label="Observation"
              value={metar.observation_time || metar.time}
              mono
            />
          </div>
        </div>
      )}

      {/* TAF */}
      {taf && (
        <div className="border-t border-zinc-800/50 pt-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
            TAF
          </h4>
          {taf.valid_from && taf.valid_to && (
            <p className="text-xxs text-gray-500 mb-2">
              Valid: {taf.valid_from} -- {taf.valid_to}
            </p>
          )}
          {(taf.raw || taf.raw_text) && (
            <div className="bg-zinc-900/50 border border-zinc-800/30 rounded-lg p-3">
              <p className="text-xs font-mono text-gray-300 leading-relaxed break-all">
                {taf.raw || taf.raw_text}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
