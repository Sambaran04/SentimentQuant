import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post('/api/v1/auth/login', credentials),
  register: (userData) => api.post('/api/v1/auth/register', userData),
  forgotPassword: (email) => api.post('/api/v1/auth/forgot-password', { email }),
  resetPassword: (data) => api.post('/api/v1/auth/reset-password', data),
};

export const tradingAPI = {
  getPortfolio: () => api.get('/api/v1/trading/portfolio'),
  getWatchlist: () => api.get('/api/v1/trading/watchlist'),
  addToWatchlist: (symbol) => api.post('/api/v1/trading/watchlist', { symbol }),
  removeFromWatchlist: (symbol) => api.delete(`/api/v1/trading/watchlist/${symbol}`),
  placeOrder: (orderData) => api.post('/api/v1/trading/orders', orderData),
  getOrders: () => api.get('/api/v1/trading/orders'),
};

export const marketAPI = {
  getStockData: (symbol) => api.get(`/api/v1/market/stocks/${symbol}`),
  getNews: () => api.get('/api/v1/market/news'),
  getSentiment: (symbol) => api.get(`/api/v1/market/sentiment/${symbol}`),
  getTechnicalIndicators: (symbol) => api.get(`/api/v1/market/technical/${symbol}`),
};

export const userAPI = {
  getProfile: () => api.get('/api/v1/users/profile'),
  updateProfile: (data) => api.put('/api/v1/users/profile', data),
  updateSettings: (settings) => api.put('/api/v1/users/settings', settings),
};

export default api; 