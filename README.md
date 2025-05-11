# SentimentQuant

SentimentQuant is an advanced trading platform that combines sentiment analysis with quantitative trading strategies. The platform analyzes market sentiment from various sources including news articles, social media, and financial reports to provide actionable trading insights.

## 🌟 Features

- **Real-time Sentiment Analysis**: Analyze market sentiment from multiple sources
- **Advanced Trading Strategies**: Implement and backtest quantitative trading strategies
- **Portfolio Management**: Track and manage your investment portfolio
- **Market Data Integration**: Access real-time market data and historical analysis
- **User Authentication**: Secure user management and authentication
- **Responsive Dashboard**: Modern, responsive UI for monitoring and trading

## 🏗️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Caching**: Redis
- **Testing**: Pytest
- **Documentation**: Swagger/OpenAPI

### Frontend
- **Framework**: React with Vite
- **State Management**: React Context + Custom Hooks
- **Styling**: Tailwind CSS
- **Charts**: Chart.js
- **API Client**: Axios
- **Testing**: Vitest
- **Build Tool**: Vite

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sentimentquant.git
   cd sentimentquant
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   - Copy `.env.example` to `.env` in both frontend and backend directories
   - Update the environment variables with your configuration

5. **Database Setup**
   ```bash
   cd backend
   alembic upgrade head
   ```

### Running the Application

1. **Start the Backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
sentimentquant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   └── package.json
└── README.md
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📚 API Documentation

The API documentation is available at `/docs` when running the backend server. It provides:
- Interactive API documentation
- Request/response examples
- Authentication requirements
- Schema definitions

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

## 📞 Support

For support, email support@sentimentquant.com or open an issue in the GitHub repository.

## 🔄 Updates

Stay updated with the latest changes by:
- Watching the repository
- Following our [Twitter](https://twitter.com/sentimentquant)
- Joining our [Discord](https://discord.gg/sentimentquant)