import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User API
export const getUsers = () => api.get('/users');
export const createUser = (userData) => api.post('/users', userData);
export const getUserById = (id) => api.get(`/users/${id}`);

// Game Results API
export const saveGameResult = (resultData) => api.post('/results', resultData);
export const getGameHistory = (userId) => api.get(`/results/user/${userId}`);
export const getUserStats = (userId) => api.get(`/results/stats/${userId}`);

// Simulation API
export const runSimulation = async (simulationParams) => {
  const response = await api.post('/simulate', simulationParams);
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
    return { error: true, message: 'No response from server. Is the backend running?', status: 0 };
  } else {
    // Error setting up request
    return { error: true, message: error.message, status: -1 };
  }
};

export default api;
