import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  CardHeader,
  Divider,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useApi } from '../hooks/useApi';
import { tradingAPI, marketAPI } from '../config/api';

const DashboardPage = () => {
  const [portfolioData, setPortfolioData] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [newsData, setNewsData] = useState([]);

  const { execute: fetchPortfolio, loading: portfolioLoading } = useApi(tradingAPI.getPortfolio);
  const { execute: fetchMarketData, loading: marketLoading } = useApi(marketAPI.getStockData);
  const { execute: fetchNews, loading: newsLoading } = useApi(marketAPI.getNews);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [portfolio, market, news] = await Promise.all([
          fetchPortfolio(),
          fetchMarketData('AAPL'), // Example: Fetching Apple stock data
          fetchNews(),
        ]);
        setPortfolioData(portfolio);
        setMarketData(market);
        setNewsData(news);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      }
    };

    loadDashboardData();
  }, [fetchPortfolio, fetchMarketData, fetchNews]);

  if (portfolioLoading || marketLoading || newsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        {/* Portfolio Overview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Portfolio Overview" />
            <Divider />
            <CardContent>
              {portfolioData ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Total Value: ${portfolioData.total_value.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Daily Change: {portfolioData.daily_change > 0 ? '+' : ''}
                    {portfolioData.daily_change}%
                  </Typography>
                </Box>
              ) : (
                <Typography>No portfolio data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Market Overview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Market Overview" />
            <Divider />
            <CardContent>
              {marketData ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {marketData.symbol}: ${marketData.price}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Change: {marketData.change > 0 ? '+' : ''}
                    {marketData.change}%
                  </Typography>
                </Box>
              ) : (
                <Typography>No market data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Price Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Price Chart
            </Typography>
            <Box sx={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={marketData?.historical_data || []}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#8884d8"
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        {/* Latest News */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Latest News" />
            <Divider />
            <CardContent>
              {newsData.length > 0 ? (
                newsData.map((news, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">{news.title}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {news.summary}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(news.published_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography>No news available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage; 