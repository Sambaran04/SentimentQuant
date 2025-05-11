# SentimentQuant Backend

A FastAPI-based backend for the SentimentQuant trading platform.

## Features

- Real-time stock data using WebSocket
- Sentiment analysis integration
- Portfolio management
- Watchlist functionality
- Price alerts and notifications
- Technical analysis indicators
- News feed integration
- Correlation analysis

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (for caching and task queue)

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sentimentquant
REDIS_URL=redis://localhost:6379/0
API_KEY=your_api_key
SECRET_KEY=your_secret_key
```

4. Initialize the database:
```bash
alembic upgrade head
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Start the Celery worker (for background tasks):
```bash
celery -A tasks worker --loglevel=info
```

3. Start the Celery beat (for scheduled tasks):
```bash
celery -A tasks beat --loglevel=info
```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/register`
- POST `/api/v1/auth/refresh`
- POST `/api/v1/auth/logout`

### Stocks
- GET `/api/v1/stocks/search`
- GET `/api/v1/prices`
- GET `/api/v1/sentiment`
- GET `/api/v1/news`
- GET `/api/v1/correlation`

### Portfolio
- GET `/api/v1/portfolio`
- GET `/api/v1/portfolio/positions`
- GET `/api/v1/portfolio/transactions`

### Watchlist
- GET `/api/v1/watchlist`
- POST `/api/v1/watchlist`
- DELETE `/api/v1/watchlist`

### Alerts
- GET `/api/v1/alerts`
- POST `/api/v1/alerts`
- PUT `/api/v1/alerts`
- DELETE `/api/v1/alerts`

## WebSocket Endpoints

- `/ws/stock/{symbol}` - Real-time stock data
- `/ws/sentiment/{symbol}` - Real-time sentiment data
- `/ws/portfolio` - Real-time portfolio updates

## Database Schema

The application uses the following main tables:
- users
- portfolios
- positions
- watchlists
- alerts
- stock_data
- sentiment_data

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
black .
isort .
flake8
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Production Deployment

1. Set up a production database
2. Configure environment variables
3. Set up a reverse proxy (e.g., Nginx)
4. Use a process manager (e.g., Supervisor)
5. Enable SSL/TLS
6. Set up monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT 