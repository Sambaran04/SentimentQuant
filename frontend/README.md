# SentimentQuant Frontend

A modern React-based frontend for the SentimentQuant trading platform.

## Environment Setup

1. Create a `.env` file in the root directory of the frontend project:

```bash
cp .env.example .env
```

2. Configure the following environment variables in your `.env` file:

### API Configuration
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Authentication
```env
VITE_AUTH_TOKEN_KEY=auth_token
VITE_REFRESH_TOKEN_KEY=refresh_token
VITE_TOKEN_EXPIRY_KEY=token_expiry
```

### Feature Flags
```env
VITE_ENABLE_REAL_TIME=true
VITE_ENABLE_ALERTS=true
VITE_ENABLE_NOTIFICATIONS=true
```

### Chart Configuration
```env
VITE_DEFAULT_TIMEFRAME=1d
VITE_DEFAULT_CHART_HEIGHT=400
VITE_DEFAULT_CHART_GRID=true
VITE_DEFAULT_CHART_TOOLTIP=true
VITE_DEFAULT_CHART_LEGEND=true
```

### WebSocket Configuration
```env
VITE_WS_RECONNECT_ATTEMPTS=5
VITE_WS_RECONNECT_INTERVAL=3000
```

### Cache Configuration
```env
VITE_CACHE_DURATION=3600
VITE_MAX_CACHE_ITEMS=100
```

### UI Configuration
```env
VITE_THEME_MODE=light
VITE_DEFAULT_LANGUAGE=en
VITE_DATE_FORMAT=YYYY-MM-DD
VITE_TIME_FORMAT=HH:mm:ss
VITE_CURRENCY=USD
```

### Development Configuration
```env
VITE_DEV_MODE=true
VITE_DEV_SERVER_PORT=3000
VITE_DEV_SERVER_HOST=localhost
```

### Production Configuration
```env
VITE_PRODUCTION_URL=https://your-production-url.com
VITE_PRODUCTION_API_URL=https://api.your-production-url.com
VITE_PRODUCTION_WS_URL=wss://ws.your-production-url.com
```

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Features

- Real-time stock data visualization
- Technical analysis with multiple indicators
- Sentiment analysis integration
- Portfolio management
- Watchlist functionality
- Price alerts and notifications
- Correlation analysis
- News feed integration

## Dependencies

- React
- Material-UI
- Recharts
- Axios
- React Router
- React Query
- WebSocket

## Development

The project uses Vite as the build tool. Key commands:

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build
- `npm run lint`: Run ESLint
- `npm run test`: Run tests

## Configuration

The application uses a centralized configuration system. All environment variables are loaded through `src/config/index.js`. This file provides:

- Default values for all configuration options
- Type conversion for numeric values
- Boolean conversion for feature flags
- API endpoint definitions
- Environment-specific settings

## API Integration

The frontend integrates with the following API endpoints:

- Authentication: `/api/v1/auth/*`
- Stocks: `/api/v1/stocks/*`
- Portfolio: `/api/v1/portfolio/*`
- Watchlist: `/api/v1/watchlist/*`
- Alerts: `/api/v1/alerts/*`

## WebSocket Integration

Real-time updates are handled through WebSocket connections:

- Stock prices: `ws://localhost:8000/ws/stock/{symbol}`
- Sentiment updates: `ws://localhost:8000/ws/sentiment/{symbol}`
- Portfolio updates: `ws://localhost:8000/ws/portfolio`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT 