import axios from 'axios';

// Single source of truth for backend communication.
// Defaults to the local backend so the app works whether it is served by the
// CRA dev server (with its package.json proxy) or a static production build
// (where the proxy does NOT exist). Override with REACT_APP_API_URL if needed.
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

export { API_BASE };
export default api;
