import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Request interceptor to add the auth token to every request
api.interceptors.request.use(
  (config) => {
    // Token is fetched from localStorage on each request, ensuring it's always up-to-date
    const token = localStorage.getItem('token');
    
    // Make sure headers object exists
    config.headers = config.headers || {};

    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Set default Content-Type if not already set
    if (!config.headers['Content-Type']) {
        config.headers['Content-Type'] = 'application/json';
    }

    return config;
  },
  (error) => {
    // Do something with request error
    return Promise.reject(error);
  }
);

export default api; 