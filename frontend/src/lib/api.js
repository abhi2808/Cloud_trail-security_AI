import axios from 'axios';
import useAuthStore from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Send a natural language query to the backend.
 * @param {string} message - The user's question
 * @param {Array} conversationHistory - Previous messages for context
 * @param {string} region - AWS region to query, or "all" for all regions
 * @param {string} account_id - Selected AWS account ID
 * @returns {Promise<Object>} QueryResponse with answer, events_count, raw_events
 */
export const postQuery = async (message, conversationHistory = [], region = 'us-east-1', account_id) => {
  const response = await api.post('/api/query', {
    message,
    conversation_history: conversationHistory,
    region,
    account_id
  });
  return response.data;
};

/**
 * Check backend health status.
 * @returns {Promise<Object>} Health status object
 */
export const checkHealth = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export default api;
