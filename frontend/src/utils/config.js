// Configuration based on environment variables or defaults
const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  apiHost: process.env.REACT_APP_HOST || 'localhost',
  apiPort: process.env.REACT_APP_PORT || '3000',
};

export default config;
