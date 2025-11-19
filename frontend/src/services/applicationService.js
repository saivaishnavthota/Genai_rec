import api, { uploadApi, publicUploadApi } from './api';

export const applicationService = {
  // Application CRUD operations
  async getApplications(params = {}) {
    // Clean up empty string parameters
    const cleanParams = {};
    Object.keys(params).forEach(key => {
      if (params[key] !== '' && params[key] !== null && params[key] !== undefined) {
        cleanParams[key] = params[key];
      }
    });
    
    const response = await api.get('/api/applications/', { params: cleanParams });
    return response.data;
  },

  async getApplication(id) {
    const response = await api.get(`/api/applications/${id}`);
    return response.data;
  },

  async getApplicationByReference(referenceNumber) {
    const response = await api.get(`/api/applications/reference/${referenceNumber}`);
    return response.data;
  },

  async updateApplication(id, data) {
    const response = await api.put(`/api/applications/${id}`, data);
    return response.data;
  },

  async updateApplicationStatus(id, status) {
    const response = await api.patch(`/api/applications/${id}/status`, { status });
    return response.data;
  },

  async rescoreApplication(id) {
    const response = await api.post(`/api/applications/${id}/rescore`);
    return response.data;
  },

  // Application submission (public)
  async submitApplication(formData) {
   const response = await publicUploadApi.post('/api/applications/apply', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Statistics
  async getApplicationStats() {
    const response = await api.get('/api/applications/stats');
    return response.data;
  }
};
