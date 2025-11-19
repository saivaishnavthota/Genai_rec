import api, { uploadApi } from './api';

export const interviewService = {
  // Fetch availability slots for candidate (uses longer timeout for email sending)
  async fetchAvailability(applicationId) {
    const response = await uploadApi.post(`/api/interviews/fetch-availability/${applicationId}`);
    return response.data;
  },

  // Get available slots for an application
  async getAvailableSlots(applicationId) {
    const response = await api.get(`/api/interviews/available-slots/${applicationId}`);
    return response.data;
  },

  // Candidate selects a slot (public endpoint)
  async selectSlot(applicationId, slotData) {
    const response = await api.post(`/api/interviews/select-slot/${applicationId}`, slotData);
    return response.data;
  },

  // Schedule interview with interviewers (uses longer timeout for email/calendar operations)
  async scheduleInterview(applicationId, interviewerData) {
    const response = await uploadApi.post(`/api/interviews/schedule-interview/${applicationId}`, interviewerData);
    return response.data;
  },

  // Mark interview as completed (uses longer timeout for review token email sending)
  async markInterviewCompleted(applicationId) {
    const response = await uploadApi.patch(`/api/interviews/mark-completed/${applicationId}`);
    return response.data;
  },

  // Get interview details
  async getInterviewDetails(applicationId) {
    const response = await api.get(`/api/interviews/details/${applicationId}`);
    return response.data;
  },

  // Get interview review
  async getInterviewReview(applicationId) {
    const response = await api.get(`/api/interviews/review/${applicationId}`);
    return response.data;
  },

  // Get all interview reviews for an application
  async getAllInterviewReviews(applicationId) {
    const response = await api.get(`/api/interviews/reviews/${applicationId}`);
    return response.data;
  },

  // Get review template
  async getReviewTemplate(applicationId) {
    const response = await api.get(`/api/interviews/review-template/${applicationId}`);
    return response.data;
  },

  // Process review email (webhook)
  async processReviewEmail(reviewData) {
    const response = await api.post('/api/interviews/process-review', reviewData);
    return response.data;
  },

  // Make final hiring decision
  async makeFinalDecision(applicationId, decision) {
    const response = await api.patch(`/api/applications/${applicationId}/final-decision`, { decision });
    return response.data;
  }
};
