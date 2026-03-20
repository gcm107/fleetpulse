import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('[FleetPulse API]', message);
    return Promise.reject(error);
  }
);

export default api;

export const searchAll = (q) => api.get('/search', { params: { q } });

export const getAirport = (code) => api.get(`/airports/${code}`);
export const getAirportWeather = (code) => api.get(`/airports/${code}/weather`);
export const getAirportNotams = (code) => api.get(`/airports/${code}/notams`);
export const getAirportRunways = (code) => api.get(`/airports/${code}/runways`);

export const getStats = () => api.get('/stats');
export const getEtlStatus = () => api.get('/etl/status');

export const getManufacturers = () => api.get('/aircraft/types/manufacturers');
export const getModels = (manufacturer) => api.get('/aircraft/types/models', { params: { manufacturer } });
export const searchByType = (manufacturer, model, limit) => api.get('/aircraft/types/search', { params: { manufacturer, model, limit } });

export const getAircraft = (nNumber) => api.get(`/aircraft/${nNumber}`);
export const getAircraftHistory = (nNumber) => api.get(`/aircraft/${nNumber}/history`);
export const getAircraftOwnership = (nNumber) => api.get(`/aircraft/${nNumber}/ownership`);
export const getAircraftSafety = (nNumber) => api.get(`/aircraft/${nNumber}/safety`);
export const getAircraftSanctions = (nNumber) => api.get(`/aircraft/${nNumber}/sanctions`);
export const searchOperators = (q, state) => api.get('/operators', { params: { q, state } });
export const getOperator = (certNumber) => api.get(`/operators/${certNumber}`);
export const getOperatorFleet = (certNumber) => api.get(`/operators/${certNumber}/fleet`);
export const getOperatorSafety = (certNumber) => api.get(`/operators/${certNumber}/safety`);
export const getOperatorEnforcement = (certNumber) => api.get(`/operators/${certNumber}/enforcement`);

export const getSafetyComparison = (operatorIds) => api.get('/safety/compare', { params: { operators: operatorIds } });

export const getLiveTracking = () => api.get('/tracking/live');
function _openskyHeaders() {
  const clientId = localStorage.getItem('opensky_client_id');
  const clientSecret = localStorage.getItem('opensky_client_secret');
  if (clientId && clientSecret) {
    return { 'X-OpenSky-Client-Id': clientId, 'X-OpenSky-Client-Secret': clientSecret };
  }
  return {};
}

export const lookupLiveAircraft = (nNumber) => api.get(`/tracking/lookup/${nNumber}`, { headers: _openskyHeaders() });
export const lookupLiveByType = (manufacturer, model) => api.get('/tracking/lookup/type', { params: { manufacturer, model }, headers: _openskyHeaders() });
export const lookupLiveByCallsign = (callsign) => api.get('/tracking/lookup/callsign', { params: { callsign }, headers: _openskyHeaders() });
export const addToWatchlist = (nNumber) => api.post('/tracking/watch', { n_number: nNumber });
export const removeFromWatchlist = (nNumber) => api.delete(`/tracking/watch/${nNumber}`);
export const getSanctionsAlerts = () => api.get('/sanctions/alerts');
export const checkSanctions = (nNumber) => api.get(`/sanctions/check/${nNumber}`);
export const triggerEtl = (module, adminKey) => {
  const headers = adminKey ? { 'X-Admin-Key': adminKey } : {};
  return api.post(`/etl/trigger/${module}`, null, { headers });
};
export const refreshWeather = (stationId) => api.get(`/weather/refresh/${stationId}`);
