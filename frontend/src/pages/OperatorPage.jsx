import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Building,
  ArrowLeft,
  FileText,
  MapPin,
  Shield,
  Gavel,
  Users,
  Check,
  X,
  Calendar,
  Hash,
  Plane,
} from 'lucide-react';
import {
  getOperator,
  getOperatorFleet,
  getOperatorEnforcement,
  getOperatorSafety,
} from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import AlertBanner from '../components/common/AlertBanner';
import FleetList from '../components/operator/FleetList';
import SafetyScorecard from '../components/safety/SafetyScorecard';
import AccidentList from '../components/safety/AccidentList';
import EnforcementHistory from '../components/operator/EnforcementHistory';
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

function AuthorityCheck({ label, granted }) {
  return (
    <div className="flex items-center gap-2">
      {granted ? (
        <div className="w-5 h-5 rounded bg-green-500/20 flex items-center justify-center">
          <Check className="w-3.5 h-3.5 text-green-400" />
        </div>
      ) : (
        <div className="w-5 h-5 rounded bg-gray-500/10 flex items-center justify-center">
          <X className="w-3.5 h-3.5 text-gray-600" />
        </div>
      )}
      <span className={`text-sm ${granted ? 'text-gray-200' : 'text-gray-500'}`}>
        {label}
      </span>
    </div>
  );
}

function certTypeVariant(type) {
  const t = (type || '').toLowerCase();
  if (t.includes('supplemental')) return 'warning';
  if (t.includes('commuter')) return 'info';
  if (t.includes('flag') || t.includes('domestic')) return 'success';
  return 'neutral';
}

function statusVariant(status) {
  const s = (status || '').toLowerCase();
  if (s.includes('active') || s.includes('valid')) return 'success';
  if (s.includes('revoked') || s.includes('cancelled') || s.includes('surrender')) return 'danger';
  if (s.includes('pending') || s.includes('suspended')) return 'warning';
  return 'neutral';
}

export default function OperatorPage() {
  const { certNumber } = useParams();
  const navigate = useNavigate();
  const [operator, setOperator] = useState(null);
  const [fleet, setFleet] = useState([]);
  const [enforcement, setEnforcement] = useState([]);
  const [safetyData, setSafetyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        const [operatorRes, fleetRes, enforcementRes, safetyRes] = await Promise.allSettled([
          getOperator(certNumber),
          getOperatorFleet(certNumber),
          getOperatorEnforcement(certNumber),
          getOperatorSafety(certNumber),
        ]);

        if (operatorRes.status === 'fulfilled') {
          setOperator(operatorRes.value.data);
        } else {
          const status = operatorRes.reason?.response?.status;
          if (status === 404) {
            setNotFound(true);
          } else {
            setError('Failed to load operator data');
          }
        }

        if (fleetRes.status === 'fulfilled') {
          const fData = fleetRes.value.data;
          setFleet(Array.isArray(fData) ? fData : fData?.fleet || fData?.aircraft || []);
        }

        if (enforcementRes.status === 'fulfilled') {
          const eData = enforcementRes.value.data;
          setEnforcement(Array.isArray(eData) ? eData : eData?.actions || eData?.enforcement || []);
        }

        if (safetyRes.status === 'fulfilled') {
          setSafetyData(safetyRes.value.data);
        }
      } catch (err) {
        setError('Failed to load operator data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [certNumber]);

  const handleAircraftClick = (row) => {
    if (row.n_number) {
      navigate(`/aircraft/${row.n_number}`);
    }
  };

  if (loading) return <LoadingSpinner message={`Loading operator ${certNumber}...`} />;

  if (notFound) {
    return (
      <div className="max-w-4xl space-y-4">
        <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <div className="card text-center py-16">
          <Building className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-100 mb-2">Operator Not Found</h1>
          <p className="text-sm text-gray-500">
            No operator found for certificate number "{certNumber}".
          </p>
        </div>
      </div>
    );
  }

  if (error && !operator) {
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

  const opStatus = operator?.status || operator?.cert_status;

  // Merge enforcement data: prefer safety response data if available, fall back to direct enforcement fetch
  const safetyEnforcement = safetyData?.enforcement_actions || safetyData?.enforcement || [];
  const mergedEnforcement = safetyEnforcement.length > 0 ? safetyEnforcement : enforcement;

  // Extract accidents from safety data
  const accidents = safetyData?.accidents || safetyData?.accident_history || [];

  return (
    <div className="max-w-7xl space-y-6">
      {/* Breadcrumb */}
      <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200">
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Operator header */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-zinc-800/50">
                <Building className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-xl font-bold text-gray-100">
                    {operator?.name || operator?.dba_name || 'Unknown Operator'}
                  </h1>
                  {operator?.cert_type && (
                    <Badge variant={certTypeVariant(operator.cert_type)}>
                      {operator.cert_type}
                    </Badge>
                  )}
                  {opStatus && (
                    <Badge variant={statusVariant(opStatus)} dot>
                      {opStatus}
                    </Badge>
                  )}
                </div>
                {operator?.dba_name && operator?.name && operator.dba_name !== operator.name && (
                  <p className="text-sm text-gray-500 mt-0.5">
                    DBA: {operator.dba_name}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Certificate number */}
          <div className="text-center">
            <p className="text-xxs text-gray-500 uppercase tracking-wider mb-0.5">Certificate</p>
            <p className="font-mono text-lg font-bold text-orange-400">
              {operator?.cert_number || certNumber}
            </p>
          </div>
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {/* Certificate info */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <FileText className="w-3.5 h-3.5" />
            Certificate Information
          </div>
          <div className="space-y-3">
            <InfoField
              label="Certificate Number"
              value={operator?.cert_number || certNumber}
              mono
              icon={Hash}
            />
            <InfoField
              label="Certificate Type"
              value={operator?.cert_type}
            />
            <InfoField
              label="Issue Date"
              value={formatDate(operator?.issue_date || operator?.cert_issue_date)}
              icon={Calendar}
              mono
            />
            <InfoField
              label="Status"
              value={opStatus}
            />
          </div>
        </div>

        {/* Location */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5" />
            Location and Operations
          </div>
          <div className="space-y-3">
            <InfoField
              label="State"
              value={operator?.state}
              icon={MapPin}
            />
            <InfoField
              label="District Office"
              value={operator?.district_office || operator?.fsdo}
            />
            <InfoField
              label="Operations Base"
              value={operator?.ops_base || operator?.base || [operator?.city, operator?.state].filter(Boolean).join(', ')}
            />
            <InfoField
              label="DOT Fitness"
              value={operator?.dot_fitness || operator?.fitness}
            />
          </div>
        </div>

        {/* Operations authority */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Users className="w-3.5 h-3.5" />
            Operations Authority
          </div>
          <div className="space-y-3">
            <AuthorityCheck
              label="Wet Lease Authority"
              granted={operator?.wet_lease === true || operator?.wet_lease === 'Y'}
            />
            <AuthorityCheck
              label="Dry Lease Authority"
              granted={operator?.dry_lease === true || operator?.dry_lease === 'Y'}
            />
            <AuthorityCheck
              label="On-Demand Operations"
              granted={operator?.on_demand === true || operator?.on_demand === 'Y'}
            />
            <AuthorityCheck
              label="Scheduled Operations"
              granted={operator?.scheduled === true || operator?.scheduled === 'Y'}
            />
            <AuthorityCheck
              label="Charter Operations"
              granted={operator?.charter === true || operator?.charter === 'Y'}
            />
          </div>
        </div>
      </div>

      {/* Fleet */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Plane className="w-3.5 h-3.5" />
          Fleet
          {fleet.length > 0 && (
            <span className="text-gray-600 font-normal">({fleet.length} aircraft)</span>
          )}
        </div>
        <FleetList fleet={fleet} onAircraftClick={handleAircraftClick} />
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
      {accidents.length > 0 && (
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Shield className="w-3.5 h-3.5" />
            Accident History
          </div>
          <AccidentList accidents={accidents} />
        </div>
      )}

      {/* Enforcement History */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Gavel className="w-3.5 h-3.5" />
          Enforcement History
        </div>
        <EnforcementHistory actions={mergedEnforcement} />
      </div>
    </div>
  );
}
