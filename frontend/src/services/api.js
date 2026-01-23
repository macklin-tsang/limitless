import axios from 'axios';

// Python backend API URL
const API_BASE_URL = process.env.REACT_APP_PYTHON_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Simulation API
export const runSimulation = async (simulationParams) => {
  const response = await api.post('/simulate', simulationParams);
  return response.data;
};

export const runSingleHand = async (params) => {
  const response = await api.post('/simulate/single', params);
  return response.data;
};

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Error handler helper
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const message = error.response.data?.message || error.response.statusText;
    return { error: true, message, status: error.response.status };
  } else if (error.request) {
    // Request was made but no response received
    return { error: true, message: 'No response from server. Is the Python backend running?', status: 0 };
  } else {
    // Error setting up request
    return { error: true, message: error.message, status: -1 };
  }
};

export default api;
