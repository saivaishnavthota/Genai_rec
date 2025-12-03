import api, { llmApi } from './api';

export const jobService = {
  // Job CRUD operations
  async getJobs(params = {}) {
    const response = await api.get('/api/jobs/', { params });
    return response.data;
  },

  async getPublicJobs(params = {}) {
    const response = await api.get('/api/jobs/public/', { params });
    return response.data;
  },

  async getJob(id) {
    const response = await api.get(`/api/jobs/${id}`);
    return response.data;
  },

  async getPublicJob(id) {
    const response = await api.get(`/api/jobs/public/${id}`);
    return response.data;
  },

  async createJob(jobData) {
    const response = await api.post('/api/jobs/', jobData);
    return response.data;
  },

  async updateJob(id, jobData) {
    const response = await api.put(`/api/jobs/${id}`, jobData);
    return response.data;
  },

  async deleteJob(id) {
    const response = await api.delete(`/api/jobs/${id}`);
    return response.data;
  },

  // AI-powered features (using longer timeout)
  async generateJobFields(data) {
    const response = await llmApi.post('/api/jobs/generate-fields', data);
    return response.data;
  },

  async generateJobDescription(data) {
    const response = await llmApi.post('/api/jobs/generate-description', data);
    return response.data;
  },

  // Job approval workflow
  async publishJob(id) {
    const response = await api.patch(`/api/jobs/${id}/publish`);
    return response.data;
  },

  async approveJob(id) {
    const response = await api.patch(`/api/jobs/${id}/approve`);
    return response.data;
  },

  // Get similar jobs for autofill
  async getSimilarJobs(jobId, limit = 5) {
    const response = await api.get(`/api/jobs/similar/${jobId}`, { params: { limit } });
    return response.data;
  }
};
