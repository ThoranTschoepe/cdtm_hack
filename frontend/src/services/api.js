import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = {
  // Create a new session
  createSession: async () => {
    const response = await axios.post(`${API_URL}/session`);
    return response.data;
  },
  
  // Get next question
  getNextQuestion: async (sessionId) => {
    const response = await axios.get(`${API_URL}/questions/${sessionId}`);
    return response.data;
  },
  
  // Submit text answer
  submitAnswer: async (sessionId, answer) => {
    const response = await axios.post(`${API_URL}/answer/${sessionId}`, answer, {
      headers: {
        'Content-Type': 'text/plain'
      }
    });
    return response.data;
  },
  
  // Upload document
  uploadDocument: async (sessionId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_URL}/document/${sessionId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  
  // Get current session state
  getSessionState: async (sessionId) => {
    const response = await axios.get(`${API_URL}/state/${sessionId}`);
    return response.data;
  },
  
  // Reset session
  resetSession: async (sessionId) => {
    const response = await axios.delete(`${API_URL}/session/${sessionId}`);
    return response.data;
  }
};

export default api;