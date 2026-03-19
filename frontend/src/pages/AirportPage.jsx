import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  MapPin,
  Navigation,
  Radio,
  Ruler,
  ArrowLeft,
  Globe,
  Mountain,
  Wind,
  Bell,
  ExternalLink,
} from 'lucide-react';
import { getAirport, getAirportRunways, getAirportWeather, getAirportNotams } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import DataTable from '../components/common/DataTable';
import AlertBanner from '../components/common/AlertBanner';
import {
  formatCoordinate,
  formatElevation,
  formatFrequency,
  formatRunwayLength,
} from '../utils/formatters';
import { AIRPORT_TYPES } from '../utils/constants';
import AirportWeather from '../components/airport/AirportWeather';
import AirportMap from '../components/airport/AirportMap';

function InfoField({ label, value, mono = false, icon: Icon }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xxs font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-1">
        {Icon && <Icon className="w-3 h-3" />}
        {label}
      </span>
      <span className={`text-sm ${mono ? 'font-mono text-blue-400' : 'text-gray-200'}`}>
        {value || '--'}
      </span>
    </div>
  );
}

export default function AirportPage() {
  const { code } = useParams();
  const [airport, setAirport] = useState(null);
  const [runways, setRunways] = useState([]);
  const [weather, setWeather] = useState(null);
  const [notams, setNotams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [airportRes, runwaysRes, weatherRes, notamsRes] = await Promise.allSettled([
          getAirport(code),
          getAirportRunways(code),
          getAirportWeather(code),
          getAirportNotams(code),
        ]);

        if (airportRes.status === 'fulfilled') {
          setAirport(airportRes.value.data);
        } else {
          setError(`Airport "${code}" not found`);
        }

        if (runwaysRes.status === 'fulfilled') {
          setRunways(runwaysRes.value.data?.runways || runwaysRes.value.data || []);
        }

        if (weatherRes.status === 'fulfilled') {
          setWeather(weatherRes.value.data);
        }

        if (notamsRes.status === 'fulfilled') {
          const notamData = notamsRes.value.data;
          setNotams(Array.isArray(notamData) ? notamData : notamData?.notams || []);
        }
      } catch (err) {
        setError('Failed to load airport data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [code]);

  if (loading) return <LoadingSpinner message={`Loading ${code}...`} />;

  if (error && !airport) {
    return (
      <div className="max-w-4xl space-y-4">
        <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <AlertBanner variant="critical" title="Error" message={error} />
      </div>
    );
  }

  const runwayColumns = [
    { key: 'le_ident', label: 'LE Ident', mono: true },
    { key: 'he_ident', label: 'HE Ident', mono: true },
    {
      key: 'length_ft',
      label: 'Length',
      mono: true,
      align: 'right',
      render: (val) => formatRunwayLength(val),
    },
    {
      key: 'width_ft',
      label: 'Width',
      mono: true,
      align: 'right',
      render: (val) => val ? `${val} ft` : '--',
    },
    { key: 'surface', label: 'Surface' },
    {
      key: 'lighted',
      label: 'Lighted',
      align: 'center',
      render: (val) =>
        val ? <Badge variant="success">Yes</Badge> : <Badge variant="neutral">No</Badge>,
    },
    {
      key: 'closed',
      label: 'Status',
      align: 'center',
      render: (val) =>
        val ? <Badge variant="danger">Closed</Badge> : <Badge variant="success">Open</Badge>,
    },
  ];

  const frequencies = airport?.frequencies || [];
  const frequencyColumns = [
    { key: 'type', label: 'Type', mono: true },
    { key: 'description', label: 'Description' },
    {
      key: 'frequency_mhz',
      label: 'Frequency (MHz)',
      mono: true,
      align: 'right',
      render: (val) => formatFrequency(val),
    },
  ];

  const typeBadge = airport?.type === 'large_airport' ? 'info' :
    airport?.type === 'medium_airport' ? 'success' :
    airport?.type === 'small_airport' ? 'warning' : 'neutral';

  return (
    <div className="max-w-7xl space-y-6">
      {/* Breadcrumb */}
      <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200">
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Airport header */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-xl font-bold text-gray-100">
                {airport?.name || code}
              </h1>
              <Badge variant={typeBadge}>
                {AIRPORT_TYPES[airport?.type] || airport?.type || 'Airport'}
              </Badge>
            </div>
            {airport?.municipality && (
              <p className="text-sm text-gray-400 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5" />
                {airport.municipality}
                {airport.iso_region ? `, ${airport.iso_region}` : ''}
                {airport.iso_country ? ` (${airport.iso_country})` : ''}
              </p>
            )}
          </div>

          {/* Code badges */}
          <div className="flex gap-3">
            {airport?.icao_code && (
              <div className="text-center">
                <p className="text-xxs text-gray-500 uppercase tracking-wider mb-0.5">ICAO</p>
                <p className="font-mono text-lg font-bold text-blue-400">{airport.icao_code}</p>
              </div>
            )}
            {airport?.iata_code && (
              <div className="text-center">
                <p className="text-xxs text-gray-500 uppercase tracking-wider mb-0.5">IATA</p>
                <p className="font-mono text-lg font-bold text-orange-400">{airport.iata_code}</p>
              </div>
            )}
            {airport?.local_code && (
              <div className="text-center">
                <p className="text-xxs text-gray-500 uppercase tracking-wider mb-0.5">FAA</p>
                <p className="font-mono text-lg font-bold text-gray-300">{airport.local_code}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Airport Map */}
      {airport?.latitude_deg != null && airport?.longitude_deg != null && (
        <AirportMap
          latitude={airport.latitude_deg}
          longitude={airport.longitude_deg}
          name={airport.name}
          icao_code={airport.icao_code}
        />
      )}

      {/* Details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Globe className="w-3.5 h-3.5" />
            Location
          </div>
          <div className="space-y-3">
            <InfoField
              label="Latitude"
              value={formatCoordinate(airport?.latitude_deg, 'lat')}
              mono
            />
            <InfoField
              label="Longitude"
              value={formatCoordinate(airport?.longitude_deg, 'lon')}
              mono
            />
            <InfoField
              label="Continent"
              value={airport?.continent}
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Mountain className="w-3.5 h-3.5" />
            Elevation
          </div>
          <div className="space-y-3">
            <InfoField
              label="Field Elevation"
              value={formatElevation(airport?.elevation_ft)}
              mono
            />
            <InfoField
              label="Identifier"
              value={airport?.ident}
              mono
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Wind className="w-3.5 h-3.5" />
            Weather
          </div>
          <AirportWeather
            metar={weather?.metar || (weather && !weather.taf ? weather : null)}
            taf={weather?.taf || null}
          />
        </div>

        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Bell className="w-3.5 h-3.5" />
            NOTAMs
          </div>
          {notams.length > 0 ? (
            <div className="space-y-2">
              {notams.slice(0, 3).map((notam, i) => (
                <div key={i} className="text-xs text-gray-400 font-mono border-l-2 border-orange-500/50 pl-2">
                  {notam.text || notam.message || JSON.stringify(notam).slice(0, 100)}
                </div>
              ))}
              {notams.length > 3 && (
                <p className="text-xxs text-gray-500">
                  +{notams.length - 3} more NOTAMs
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              No active NOTAMs. NOTAM data updates periodically.
            </p>
          )}
        </div>
      </div>

      {/* Runways */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Navigation className="w-3.5 h-3.5" />
          Runways
        </div>
        <DataTable
          columns={runwayColumns}
          data={Array.isArray(runways) ? runways : []}
          emptyMessage="No runway data available for this airport"
        />
      </div>

      {/* Frequencies */}
      {frequencies.length > 0 && (
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Radio className="w-3.5 h-3.5" />
            Frequencies
          </div>
          <DataTable
            columns={frequencyColumns}
            data={frequencies}
            emptyMessage="No frequency data available"
          />
        </div>
      )}

      {/* External link */}
      {airport?.home_link && (
        <div className="card bg-zinc-900/50">
          <a
            href={airport.home_link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300"
          >
            <ExternalLink className="w-4 h-4" />
            Visit Airport Website
          </a>
        </div>
      )}
    </div>
  );
}
