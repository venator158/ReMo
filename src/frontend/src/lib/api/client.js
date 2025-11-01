import axios from 'axios';
import { get } from 'svelte/store';
import { token } from '../../stores/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
client.interceptors.request.use(
  (config) => {
    const authToken = get(token);
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth endpoints
export const auth = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await client.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  register: async (username, email, password) => {
    const response = await client.post('/api/auth/register', {
      username,
      email,
      password,
    });
    return response.data;
  },
  getMe: async () => {
    const response = await client.get('/api/auth/me');
    return response.data;
  },
};

// Node endpoints
export const nodes = {
  getAll: async () => {
    const response = await client.get('/api/nodes');
    return response.data;
  },
  getOne: async (nodeId) => {
    const response = await client.get(`/api/nodes/${nodeId}`);
    return response.data;
  },
  authenticate: async (nodeId, password) => {
    const response = await client.post('/api/nodes/authenticate', {
      node_id: nodeId,
      password: password,
    });
    return response.data;
  },
};

// Metrics endpoints
export const metrics = {
  getLatest: async (nodeId = null, nodePassword = null) => {
    const params = {};
    if (nodeId) {
      params.node_id = nodeId;
      if (nodePassword) params.node_password = nodePassword;
    }
    const response = await client.get('/api/metrics/latest', { params });
    return response.data;
  },
  getHistory: async (nodeId, nodePassword, metricType = null, hours = 1) => {
    const params = { node_id: nodeId, node_password: nodePassword, hours };
    if (metricType) params.metric_type = metricType;
    const response = await client.get('/api/metrics/history', { params });
    return response.data;
  },
};

// Threshold endpoints
export const thresholds = {
  getAll: async (nodeId = null) => {
    const params = nodeId ? { node_id: nodeId } : {};
    const response = await client.get('/api/thresholds', { params });
    return response.data;
  },
  create: async (nodeId, metricType, thresholdValue, condition) => {
    const response = await client.post('/api/thresholds', {
      node_id: nodeId,
      metric_type: metricType,
      threshold_value: thresholdValue,
      condition,
    });
    return response.data;
  },
  delete: async (thresholdId) => {
    const response = await client.delete(`/api/thresholds/${thresholdId}`);
    return response.data;
  },
};

// Alert endpoints
export const alerts = {
  getAll: async (nodeId = null, acknowledged = null, limit = 100) => {
    const params = { limit };
    if (nodeId) params.node_id = nodeId;
    if (acknowledged !== null) params.acknowledged = acknowledged;
    const response = await client.get('/api/alerts', { params });
    return response.data;
  },
  acknowledge: async (alertId) => {
    const response = await client.post(`/api/alerts/${alertId}/acknowledge`);
    return response.data;
  },
};

// Dashboard endpoints
export const dashboard = {
  getStats: async () => {
    const response = await client.get('/api/dashboard/stats');
    return response.data;
  },
};

// Export endpoints
export const exportData = {
  downloadCSV: async (nodeId = null, metricType = null, hours = 24) => {
    const params = { hours };
    if (nodeId) params.node_id = nodeId;
    if (metricType) params.metric_type = metricType;
    const response = await client.get('/api/export/csv', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
  getSummary: async (nodeId = null, hours = 24) => {
    const params = { hours };
    if (nodeId) params.node_id = nodeId;
    const response = await client.get('/api/export/summary', { params });
    return response.data;
  },
};

export default client;
