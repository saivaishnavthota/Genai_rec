import axios from 'axios';
import config from '../utils/config';

const API_BASE_URL = config.apiUrl || 'http://localhost:8000';

// Create axios instance with JWT headers
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface StartInterviewRequest {
  application_id: number;
  job_id: number;
}

export interface StartInterviewResponse {
  session_id: number;
  webrtc_token?: string;
  policy_version: string;
  rubric_version: string;
}

export interface ClientEvent {
  event_type: 'head_pose' | 'face_present' | 'multi_face' | 'phone' | 'tab_switch';
  timestamp: number;
  confidence: number;
  metadata?: Record<string, any>;
  yaw?: number;
  pitch?: number;
  roll?: number;
  face_count?: number;
  phone_detected?: boolean;
  tab_visible?: boolean;
}

export interface Flag {
  id: number;
  session_id: number;
  flag_type: string;
  severity: 'low' | 'moderate' | 'high';
  confidence: number;
  t_start: number;
  t_end: number;
  clip_url?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface SessionReport {
  session: {
    id: number;
    application_id: number;
    job_id: number;
    status: string;
    total_score?: number;
    recommendation?: 'pass' | 'review' | 'fail';
    transcript_url?: string;
    video_url?: string;
    report_json?: any;
  };
  flags: Flag[];
  transcript?: any;
  scores?: {
    criteria: Array<{
      criterion_name: string;
      score: number;
      explanation: string;
      citations: any[];
    }>;
    final_score: number;
    citations: any[];
    summary: string;
    improvement_tip?: string;
  };
}

export interface ReviewDecision {
  status: 'PASS' | 'REVIEW' | 'FAIL';
  notes?: string;
}

// API methods
export const aiInterviewAPI = {
  startInterview: async (data: StartInterviewRequest): Promise<StartInterviewResponse> => {
    const response = await apiClient.post('/api/ai-interview/start', data);
    return response.data;
  },

  postClientEvents: async (sessionId: number, events: ClientEvent[]): Promise<void> => {
    await apiClient.post(`/api/ai-interview/${sessionId}/events`, { events });
  },

  endInterview: async (sessionId: number): Promise<void> => {
    await apiClient.post(`/api/ai-interview/${sessionId}/end`);
  },

  getReport: async (sessionId: number): Promise<SessionReport> => {
    const response = await apiClient.get(`/api/ai-interview/${sessionId}/report`);
    return response.data;
  },

  getFlags: async (sessionId: number): Promise<Flag[]> => {
    const response = await apiClient.get(`/api/ai-interview/${sessionId}/flags`);
    return response.data;
  },

  getQuestions: async (sessionId: number): Promise<{ questions: Question[]; total: number; job_title: string }> => {
    const response = await apiClient.get(`/api/ai-interview/${sessionId}/questions`);
    return response.data;
  },

  getApplicationAISessions: async (applicationId: number): Promise<{ application_id: number; sessions: any[]; total: number }> => {
    const response = await apiClient.get(`/api/ai-interview/application/${applicationId}/sessions`);
    return response.data;
  },

  triggerScoring: async (sessionId: number): Promise<any> => {
    const response = await apiClient.post(`/api/ai-interview/${sessionId}/score`);
    return response.data;
  },

  postReviewDecision: async (sessionId: number, decision: ReviewDecision): Promise<void> => {
    await apiClient.post(`/api/ai-interview/review/${sessionId}/decision`, decision);
  },
};

export interface Question {
  id: number;
  text: string;
  type: 'behavioral' | 'technical' | 'experience' | 'closing';
  time_limit: number; // in seconds
}

export default apiClient;

