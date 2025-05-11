import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds timeout
});

// Request interceptor for adding auth token
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

// Response interceptor for handling errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Get new token
        const response = await api.post('/api/v1/auth/refresh-token');
        const { token } = response.data;
        localStorage.setItem('token', token);

        // Update the failed request's authorization header
        originalRequest.headers.Authorization = `Bearer ${token}`;

        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh token fails, redirect to login
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    if (error.response?.status === 403) {
      // Handle forbidden access
      console.error('Access forbidden');
    } else if (error.response?.status === 429) {
      // Handle rate limiting
      console.error('Too many requests');
    }

    return Promise.reject(error);
  }
);

// Add retry logic for failed requests
const retryRequest = async (fn, retries = 3, delay = 1000) => {
  try {
    return await fn();
  } catch (error) {
    if (retries === 0) throw error;
    await new Promise(resolve => setTimeout(resolve, delay));
    return retryRequest(fn, retries - 1, delay * 2);
  }
};

// API endpoints
export const authAPI = {
  login: (credentials) => retryRequest(() => api.post('/api/v1/auth/login', credentials)),
  register: (userData) => retryRequest(() => api.post('/api/v1/auth/register', userData)),
  forgotPassword: (email) => retryRequest(() => api.post('/api/v1/auth/forgot-password', { email })),
  resetPassword: (data) => retryRequest(() => api.post('/api/v1/auth/reset-password', data)),
  refreshToken: () => retryRequest(() => api.post('/api/v1/auth/refresh-token')),
};

export const tradingAPI = {
  getPortfolio: () => retryRequest(() => api.get('/api/v1/trading/portfolio')),
  getWatchlist: () => retryRequest(() => api.get('/api/v1/trading/watchlist')),
  addToWatchlist: (symbol) => retryRequest(() => api.post('/api/v1/trading/watchlist', { symbol })),
  removeFromWatchlist: (symbol) => retryRequest(() => api.delete(`/api/v1/trading/watchlist/${symbol}`)),
  placeOrder: (orderData) => retryRequest(() => api.post('/api/v1/trading/orders', orderData)),
  getOrders: () => retryRequest(() => api.get('/api/v1/trading/orders')),
};

export const marketAPI = {
  getStockData: (symbol) => retryRequest(() => api.get(`/api/v1/market/stocks/${symbol}`)),
  getNews: () => retryRequest(() => api.get('/api/v1/market/news')),
  getSentiment: (symbol) => retryRequest(() => api.get(`/api/v1/market/sentiment/${symbol}`)),
  getTechnicalIndicators: (symbol) => retryRequest(() => api.get(`/api/v1/market/technical/${symbol}`)),
};

export const userAPI = {
  getProfile: () => retryRequest(() => api.get('/api/v1/users/profile')),
  updateProfile: (data) => retryRequest(() => api.put('/api/v1/users/profile', data)),
  updateSettings: (settings) => retryRequest(() => api.put('/api/v1/users/settings', settings)),
};

export default api; 