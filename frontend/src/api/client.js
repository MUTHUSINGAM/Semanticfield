import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  me: () => api.get('/api/auth/me'),
  demoCredentials: () => api.get('/api/auth/demo-credentials'),
};

export const chatAPI = {
  send: (message) => api.post('/api/chat', { message }),
};

export const dashboardAPI = {
  stats: () => api.get('/api/dashboard/stats'),
  activities: () => api.get('/api/dashboard/recent-activities'),
  topSources: () => api.get('/api/dashboard/top-sources'),
};

export const auditAPI = {
  logs: () => api.get('/api/audit-logs'),
  policies: () => api.get('/api/policies'),
  updatePolicies: (data) => api.put('/api/policies', data),
};

export const sourcesAPI = {
  list: () => api.get('/api/sources'),
  ingest: () => api.post('/api/sources/ingest'),
  mcpStatus: () => api.get('/api/sources/mcp-status'),
  syncStatus: () => api.get('/api/sources/sync-status'),
  slackVerify: () => api.get('/api/sources/slack/verify'),
};

export const healthAPI = {
  check: () => api.get('/api/health'),
};
