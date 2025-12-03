import axios from 'axios';
import config from '../utils/config';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: config.apiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for LLM/AI operations with longer timeout
export const llmApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 120000, // 2 minutes for LLM operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for file uploads with longer timeout
export const uploadApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 60000, // 1 minute for file uploads and processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for public file uploads (no auth required)
export const publicUploadApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 180000, // 3 minutes for file uploads and processing (resume parsing + scoring can be slow)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for public API endpoints (no auth required)
export const publicApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});
// Request interceptor to add auth token (for regular API)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Request interceptor to add auth token (for LLM API)
llmApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Request interceptor to add auth token (for Upload API)
uploadApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors (for regular API)
api.interceptors.response.use(
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

// Response interceptor to handle errors (for LLM API)
llmApi.interceptors.response.use(
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

// Response interceptor to handle errors (for Upload API)
uploadApi.interceptors.response.use(
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

// Response interceptor to handle errors (for Public Upload API - no auth redirect)
publicUploadApi.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't redirect to login for public endpoints
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors (for Public API - no auth redirect)
publicApi.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't redirect to login for public endpoints
    return Promise.reject(error);
  }
);

export default api;
