const config = {
  // API Configuration
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',

  // Authentication
  authTokenKey: import.meta.env.VITE_AUTH_TOKEN_KEY || 'auth_token',
  refreshTokenKey: import.meta.env.VITE_REFRESH_TOKEN_KEY || 'refresh_token',
  tokenExpiryKey: import.meta.env.VITE_TOKEN_EXPIRY_KEY || 'token_expiry',

  // Feature Flags
  enableRealTime: import.meta.env.VITE_ENABLE_REAL_TIME === 'true',
  enableAlerts: import.meta.env.VITE_ENABLE_ALERTS === 'true',
  enableNotifications: import.meta.env.VITE_ENABLE_NOTIFICATIONS === 'true',

  // Chart Configuration
  defaultTimeframe: import.meta.env.VITE_DEFAULT_TIMEFRAME || '1d',
  defaultChartHeight: parseInt(import.meta.env.VITE_DEFAULT_CHART_HEIGHT || '400', 10),
  defaultChartGrid: import.meta.env.VITE_DEFAULT_CHART_GRID !== 'false',
  defaultChartTooltip: import.meta.env.VITE_DEFAULT_CHART_TOOLTIP !== 'false',
  defaultChartLegend: import.meta.env.VITE_DEFAULT_CHART_LEGEND !== 'false',

  // WebSocket Configuration
  wsReconnectAttempts: parseInt(import.meta.env.VITE_WS_RECONNECT_ATTEMPTS || '5', 10),
  wsReconnectInterval: parseInt(import.meta.env.VITE_WS_RECONNECT_INTERVAL || '3000', 10),

  // Cache Configuration
  cacheDuration: parseInt(import.meta.env.VITE_CACHE_DURATION || '3600', 10),
  maxCacheItems: parseInt(import.meta.env.VITE_MAX_CACHE_ITEMS || '100', 10),

  // UI Configuration
  themeMode: import.meta.env.VITE_THEME_MODE || 'light',
  defaultLanguage: import.meta.env.VITE_DEFAULT_LANGUAGE || 'en',
  dateFormat: import.meta.env.VITE_DATE_FORMAT || 'YYYY-MM-DD',
  timeFormat: import.meta.env.VITE_TIME_FORMAT || 'HH:mm:ss',
  currency: import.meta.env.VITE_CURRENCY || 'USD',

  // Analytics Configuration
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  analyticsId: import.meta.env.VITE_ANALYTICS_ID,

  // Error Reporting
  enableErrorReporting: import.meta.env.VITE_ENABLE_ERROR_REPORTING === 'true',
  errorReportingUrl: import.meta.env.VITE_ERROR_REPORTING_URL,

  // Development Configuration
  isDev: import.meta.env.DEV,
  devServerPort: parseInt(import.meta.env.VITE_DEV_SERVER_PORT || '3000', 10),
  devServerHost: import.meta.env.VITE_DEV_SERVER_HOST || 'localhost',

  // Production Configuration
  productionUrl: import.meta.env.VITE_PRODUCTION_URL,
  productionApiUrl: import.meta.env.VITE_PRODUCTION_API_URL,
  productionWsUrl: import.meta.env.VITE_PRODUCTION_WS_URL,

  // API Endpoints
  endpoints: {
    auth: {
      login: '/api/v1/auth/login',
      register: '/api/v1/auth/register',
      refresh: '/api/v1/auth/refresh',
      logout: '/api/v1/auth/logout',
    },
    stocks: {
      search: '/api/v1/stocks/search',
      price: '/api/v1/prices',
      sentiment: '/api/v1/sentiment',
      news: '/api/v1/news',
      correlation: '/api/v1/correlation',
    },
    portfolio: {
      summary: '/api/v1/portfolio',
      positions: '/api/v1/portfolio/positions',
      transactions: '/api/v1/portfolio/transactions',
    },
    watchlist: {
      list: '/api/v1/watchlist',
      add: '/api/v1/watchlist',
      remove: '/api/v1/watchlist',
    },
    alerts: {
      list: '/api/v1/alerts',
      create: '/api/v1/alerts',
      update: '/api/v1/alerts',
      delete: '/api/v1/alerts',
    },
  },
};

export default config; 