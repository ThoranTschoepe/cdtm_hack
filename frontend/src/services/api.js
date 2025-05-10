// services/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = {
  // Create a new session
  createSession: async () => {
    const response = await axios.post(`${API_URL}/session`);
    return response.data;
  },

  // Get the next question - now includes audio URL
  getNextQuestion: async (sessionId) => {
    const response = await axios.get(`${API_URL}/questions/${sessionId}`);
    return response.data;
  },

  // Legacy method - kept for backward compatibility
  getNextQuestionAudio: async (sessionId) => {
    // This will now use the audio_url from the question response
    // But we'll implement it in a backward-compatible way
    try {
      // First try to get the JSON response which includes the audio URL
      const response = await axios.get(`${API_URL}/questions/${sessionId}`);
      // If we have an audio_url, use it
      if (response.data.audio_url) {
        const audioResponse = await fetch(`${API_URL}${response.data.audio_url}`);
        const blob = await audioResponse.blob();
        return URL.createObjectURL(blob);
      }
    } catch (error) {
      console.warn("Error:", error);
    }
  },

  // Submit an answer
  submitAnswer: async (sessionId, answer) => {
    const response = await axios.post(`${API_URL}/answer/${sessionId}`, {
      answer
    });
    return response.data;
  },

  // Upload a single document (for backward compatibility)
  uploadDocument: async (sessionId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(
      `${API_URL}/document-single/${sessionId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  // Upload multiple documents
  uploadDocuments: async (sessionId, files) => {
    // If "skip" is passed, submit the skip answer
    if (files === "skip") {
      return await api.submitAnswer(sessionId, "skip");
    }

    const formData = new FormData();
    
    // Handle single file or array of files
    if (Array.isArray(files)) {
      // Append each file to the form data with the same field name
      files.forEach(file => {
        formData.append('files', file);
      });
    } else {
      // If a single file is passed, append it
      formData.append('files', files);
    }

    const response = await axios.post(
      `${API_URL}/document/${sessionId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  // Reset a session
  resetSession: async (sessionId) => {
    const response = await axios.delete(`${API_URL}/session/${sessionId}`);
    return response.data;
  },

  // Get current session state (for debugging)
  getSessionState: async (sessionId) => {
    const response = await axios.get(`${API_URL}/state/${sessionId}`);
    return response.data;
  }
};

export default api;