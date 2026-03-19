import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  PlaneTakeoff,
  ArrowLeft,
  Info,
  User,
  History,
  Link2,
  Shield,
  AlertTriangle,
  Calendar,
  Hash,
  Gauge,
  Cog,
  MapPin,
} from 'lucide-react';
import {
  getAircraft,
  getAircraftHistory,
  getAircraftOwnership,
  getAircraftSafety,
  getAircraftSanctions,
} from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import AlertBanner from '../components/common/AlertBanner';
import AircraftTimeline from '../components/aircraft/AircraftTimeline';
import OwnershipChain from '../components/aircraft/OwnershipChain';
import SafetyScorecard from '../components/safety/SafetyScorecard';
import AccidentList from '../components/safety/AccidentList';
import SanctionsCheck from '../components/sanctions/SanctionsCheck';
import { formatDate } from '../utils/formatters';

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

function statusVariant(status) {
  const s = (status || '').toLowerCase();
  if (s.includes('valid') || s.includes('active')) return 'success';
  if (s.includes('expired') || s.includes('revoked') || s.includes('cancel')) return 'danger';
  if (s.includes('pending') || s.includes('suspended')) return 'warning';
  return 'neutral';
}

function registrantTypeLabel(code) {
  const types = {
    1: 'Individual',
    2: 'Partnership',
    3: 'Corporation',
    4: 'Co-Owned',
    5: 'Government',
    7: 'LLC',
    8: 'Non-Citizen Corporation',
    9: 'Non-Citizen Co-Owned',
  };
  return types[code] || code || '--';
}

function aircraftTypeLabel(code) {
  const types = {
    1: 'Glider',
    2: 'Balloon',
    3: 'Blimp/Dirigible',
    4: 'Fixed Wing Single-Engine',
    5: 'Fixed Wing Multi-Engine',
    6: 'Rotorcraft',
    7: 'Weight-Shift-Control',
    8: 'Powered Parachute',
    9: 'Gyroplane',
  };
  return types[code] || code || '--';
}

function engineTypeLabel(code) {
  const types = {
    0: 'None',
    1: 'Reciprocating',
    2: 'Turbo-Prop',
    3: 'Turbo-Shaft',
    4: 'Turbo-Jet',
    5: 'Turbo-Fan',
    6: 'Ramjet',
    7: '2 Cycle',
    8: '4 Cycle',
    9: 'Unknown',
    10: 'Electric',
    11: 'Rotary',
  };
  return types[code] || code || '--';
}

export default function AircraftPage() {
  const { nNumber } = useParams();
  const [aircraft, setAircraft] = useState(null);
  const [history, setHistory] = useState([]);
  const [ownership, setOwnership] = useState([]);
  const [safetyData, setSafetyData] = useState(null);
  const [sanctionsData, setSanctionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        const [aircraftRes, historyRes, ownershipRes, safetyRes, sanctionsRes] = await Promise.allSettled([
          getAircraft(nNumber),
          getAircraftHistory(nNumber),
          getAircraftOwnership(nNumber),
          getAircraftSafety(nNumber),
          getAircraftSanctions(nNumber),
        ]);

        if (aircraftRes.status === 'fulfilled') {
          setAircraft(aircraftRes.value.data);
        } else {
          const status = aircraftRes.reason?.response?.status;
          if (status === 404) {
            setNotFound(true);
          } else {
            setError('Failed to load aircraft data');
          }
        }

        if (historyRes.status === 'fulfilled') {
          const hData = historyRes.value.data;
          setHistory(Array.isArray(hData) ? hData : hData?.events || hData?.history || []);
        }

        if (ownershipRes.status === 'fulfilled') {
          const oData = ownershipRes.value.data;
          setOwnership(Array.isArray(oData) ? oData : oData?.records || oData?.ownership || []);
        }

        if (safetyRes.status === 'fulfilled') {
          setSafetyData(safetyRes.value.data);
        }

        if (sanctionsRes.status === 'fulfilled') {
          setSanctionsData(sanctionsRes.value.data);
        }
      } catch (err) {
        setError('Failed to load aircraft data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [nNumber]);

  if (loading) return <LoadingSpinner message={`Loading N${nNumber}...`} />;

  if (notFound) {
    return (
      <div className="max-w-4xl space-y-4">
        <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <div className="card text-center py-16">
          <PlaneTakeoff className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-100 mb-2">Aircraft Not Found</h1>
          <p className="text-sm text-gray-500">
            No FAA registration found for N-number "{nNumber}".
          </p>
        </div>
      </div>
    );
  }

  if (error && !aircraft) {
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

  const regStatus = aircraft?.status || aircraft?.registration_status || aircraft?.cert_status;

  return (
    <div className="max-w-7xl space-y-6">
      {/* Breadcrumb */}
      <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200">
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Sanctions alert banner at top */}
      {sanctionsData && (sanctionsData.has_match || (sanctionsData.matches && sanctionsData.matches.length > 0)) && (
        <AlertBanner
          variant="critical"
          title="Sanctions Match Detected"
          message={`This aircraft has ${sanctionsData.matches?.length || 0} potential match(es) against the OFAC SDN list. Review the sanctions section below for details.`}
        />
      )}

      {/* Aircraft header */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-zinc-800/50">
                <PlaneTakeoff className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-bold text-gray-100 font-mono">
                    N{aircraft?.n_number || nNumber}
                  </h1>
                  {regStatus && (
                    <Badge variant={statusVariant(regStatus)} dot>
                      {regStatus}
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-400 mt-0.5">
                  {[aircraft?.manufacturer, aircraft?.model].filter(Boolean).join(' ') || 'Unknown Aircraft'}
                  {aircraft?.year_mfr ? ` (${aircraft.year_mfr})` : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Serial / Mode S */}
          <div className="flex gap-6">
            {aircraft?.serial_number && (
              <div className="text-center">
                <p className="text-xxs text-gray-500 uppercase tracking-wider mb-0.5">Serial</p>
                <p className="font-mono text-lg font-bold text-gray-300">{aircraft.serial_number}</p>
              </div>
            )}
            {aircraft?.transponder_hex && (
              <div className="text-center">
                <p className="text-xxs text-gray-500 uppercase tracking-wider mb-0.5">Mode S Hex</p>
                <p className="font-mono text-lg font-bold text-blue-400">
                  {aircraft.transponder_hex}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {/* Aircraft info */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Info className="w-3.5 h-3.5" />
            Aircraft Information
          </div>
          <div className="space-y-3">
            <InfoField
              label="Aircraft Type"
              value={aircraft?.aircraft_type}
              icon={PlaneTakeoff}
            />
            <InfoField
              label="Engine Type"
              value={aircraft?.engine_type}
              icon={Cog}
            />
            <InfoField
              label="Engine Model"
              value={aircraft?.engine_model}
              mono
            />
            <InfoField
              label="Number of Engines"
              value={aircraft?.engine_count}
              mono
            />
            <InfoField
              label="Number of Seats"
              value={aircraft?.number_of_seats}
              mono
            />
          </div>
        </div>

        {/* Registration info */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Hash className="w-3.5 h-3.5" />
            Registration Details
          </div>
          <div className="space-y-3">
            <InfoField
              label="N-Number"
              value={aircraft?.n_number ? `N${aircraft.n_number}` : '--'}
              mono
            />
            <InfoField
              label="Serial Number"
              value={aircraft?.serial_number}
              mono
            />
            <InfoField
              label="Mode S Code (Hex)"
              value={aircraft?.transponder_hex}
              mono
            />
            <InfoField
              label="Certificate Issue Date"
              value={formatDate(aircraft?.cert_issue_date)}
              icon={Calendar}
              mono
            />
            <InfoField
              label="Airworthiness Date"
              value={formatDate(aircraft?.airworthiness_date)}
              icon={Calendar}
              mono
            />
            <InfoField
              label="Airworthiness Class"
              value={aircraft?.airworthiness_class}
            />
          </div>
        </div>

        {/* Registrant info */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <User className="w-3.5 h-3.5" />
            Registrant
          </div>
          <div className="space-y-3">
            <InfoField
              label="Name"
              value={aircraft?.registrant_name}
            />
            <InfoField
              label="Type"
              value={aircraft?.registrant_type}
            />
            <InfoField
              label="Street"
              value={aircraft?.registrant_street}
            />
            <InfoField
              label="City"
              value={aircraft?.registrant_city}
              icon={MapPin}
            />
            <InfoField
              label="State"
              value={aircraft?.registrant_state}
            />
            <InfoField
              label="ZIP"
              value={aircraft?.registrant_zip}
              mono
            />
            <InfoField
              label="Country"
              value={aircraft?.registrant_country || aircraft?.country_code || 'US'}
            />
          </div>
        </div>
      </div>

      {/* Tail Number History */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <History className="w-3.5 h-3.5" />
          Registration History
        </div>
        <AircraftTimeline events={history} />
      </div>

      {/* Ownership */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Link2 className="w-3.5 h-3.5" />
          Ownership Chain
        </div>
        <OwnershipChain records={ownership} />
      </div>

      {/* Safety Score */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Shield className="w-3.5 h-3.5" />
          Safety Score
        </div>
        <SafetyScorecard score={safetyData?.score || safetyData?.safety_score || null} />
      </div>

      {/* Accident History */}
      {safetyData && (
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5" />
            Accident History
          </div>
          <AccidentList
            accidents={
              safetyData?.accidents || safetyData?.accident_history || []
            }
          />
        </div>
      )}

      {/* Sanctions check */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5" />
          Sanctions Screening
        </div>
        <SanctionsCheck result={sanctionsData} />
      </div>
    </div>
  );
}
