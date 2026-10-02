import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const apiService = {
  // Check backend health
  checkHealth: async () => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },

  // Get all saved assessments
  getAssessments: async () => {
    const response = await apiClient.get('/api/assessments');
    return response.data;
  },

  // Create a new assessment
  createAssessment: async (locationData) => {
    const response = await apiClient.post('/api/assessments', locationData);
    return response.data;
  },

  // Get assessment details by ID
  getAssessmentById: async (id) => {
    const response = await apiClient.get(`/api/assessments/${id}`);
    return response.data;
  },
};

export default apiClient;
