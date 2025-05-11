import React, { useState, useEffect, useCallback } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Card,
  CardContent,
  IconButton,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import axios from 'axios';
import LineChart from '../components/charts/LineChart';
import CandlestickChart from '../components/charts/CandlestickChart';
import BarChart from '../components/charts/BarChart';
import TechnicalChart from '../components/charts/TechnicalChart';
import CorrelationMatrix from '../components/charts/CorrelationMatrix';
import DataTable from '../components/tables/DataTable';
import useWebSocket from '../hooks/useWebSocket';
import SearchBar from '../components/SearchBar';
import NewsFeed from '../components/NewsFeed';
import Watchlist from '../components/Watchlist';

const DashboardPage = () => {
  const [loading, setLoading] = useState(false);
  const [sentimentData, setSentimentData] = useState([]);
  const [priceData, setPriceData] = useState([]);
  const [portfolioData, setPortfolioData] = useState([]);
  const [error, setError] = useState(null);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [timeframe, setTimeframe] = useState('1d');
  const [volumeData, setVolumeData] = useState([]);
  const [summaryData, setSummaryData] = useState({
    portfolioValue: 0,
    sentimentScore: 0,
    activePositions: 0,
  });
  const [activeTab, setActiveTab] = useState(0);

  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'];
  const timeframes = [
    { value: '1d', label: '1 Day' },
    { value: '1w', label: '1 Week' },
    { value: '1m', label: '1 Month' },
    { value: '3m', label: '3 Months' },
    { value: '1y', label: '1 Year' },
  ];

  const fetchData = useCallback(async () => {
    if (!selectedSymbol) return;

    try {
      setLoading(true);
      setError(null);

      const [priceResponse, sentimentResponse, portfolioResponse] = await Promise.all([
        axios.get(`/api/v1/prices/${selectedSymbol}?timeframe=${timeframe}`),
        axios.get(`/api/v1/sentiment/${selectedSymbol}?timeframe=${timeframe}`),
        axios.get('/api/v1/portfolio'),
      ]);

      setPriceData(priceResponse.data);
      setSentimentData(sentimentResponse.data);
      setPortfolioData(portfolioResponse.data.positions);
      setSummaryData({
        portfolioValue: portfolioResponse.data.totalValue,
        sentimentScore: sentimentResponse.data.averageScore,
        activePositions: portfolioResponse.data.positions.length,
      });

      // Process volume data from price data
      const volumeData = priceData.map(item => ({
        date: item.date,
        volume: item.volume,
      }));
      setVolumeData(volumeData);
    } catch (err) {
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, timeframe]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // WebSocket connection for real-time updates
  const { lastMessage } = useWebSocket('trading', selectedSymbol);

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      if (data.type === 'price') {
        setPriceData(prev => [...prev, data.price]);
      } else if (data.type === 'sentiment') {
        setSentimentData(prev => [...prev, data.sentiment]);
      }
    }
  }, [lastMessage]);

  const handleSymbolChange = (symbol) => {
    setSelectedSymbol(symbol);
  };

  const handleTimeframeChange = (event) => {
    setTimeframe(event.target.value);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const portfolioColumns = [
    { id: 'symbol', label: 'Symbol', sortable: true },
    { id: 'quantity', label: 'Quantity', sortable: true },
    { id: 'avgPrice', label: 'Avg. Price', sortable: true },
    { id: 'currentPrice', label: 'Current Price', sortable: true },
    {
      id: 'pl',
      label: 'P/L',
      sortable: true,
      render: (row) => (
        <Typography
          color={row.pl >= 0 ? 'success.main' : 'error.main'}
          sx={{ display: 'flex', alignItems: 'center' }}
        >
          {row.pl >= 0 ? '+' : ''}{row.pl}%
        </Typography>
      ),
    },
  ];

  if (loading && !selectedSymbol) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {/* Search and Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ flexGrow: 1 }}>
              <SearchBar onSymbolSelect={handleSymbolChange} />
            </Box>
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Timeframe</InputLabel>
              <Select
                value={timeframe}
                label="Timeframe"
                onChange={handleTimeframeChange}
              >
                {timeframes.map((tf) => (
                  <MenuItem key={tf.value} value={tf.value}>
                    {tf.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <IconButton onClick={fetchData} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Paper>
        </Grid>

        {/* Watchlist */}
        <Grid item xs={12} md={3}>
          <Watchlist onSymbolSelect={handleSymbolChange} />
        </Grid>

        {/* Summary Cards */}
        <Grid item xs={12} md={9}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Portfolio Value
                  </Typography>
                  <Typography variant="h4">
                    ${summaryData.portfolioValue.toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Sentiment Score
                  </Typography>
                  <Typography variant="h4">
                    {summaryData.sentimentScore.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Active Positions
                  </Typography>
                  <Typography variant="h4">
                    {summaryData.activePositions}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Charts and Analysis */}
        {selectedSymbol && (
          <>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Tabs value={activeTab} onChange={handleTabChange}>
                  <Tab label="Technical Analysis" />
                  <Tab label="Price History" />
                  <Tab label="Volume" />
                  <Tab label="Sentiment" />
                </Tabs>
                <Box sx={{ mt: 2 }}>
                  {activeTab === 0 && (
                    <TechnicalChart
                      data={priceData}
                      title={`${selectedSymbol} Technical Analysis`}
                      height={400}
                    />
                  )}
                  {activeTab === 1 && (
                    <CandlestickChart
                      data={priceData}
                      title={`${selectedSymbol} Price History`}
                      height={400}
                    />
                  )}
                  {activeTab === 2 && (
                    <BarChart
                      data={volumeData}
                      title="Volume"
                      xAxisKey="date"
                      yAxisKey="volume"
                      height={400}
                    />
                  )}
                  {activeTab === 3 && (
                    <LineChart
                      data={sentimentData}
                      title="Sentiment Trend"
                      xAxisKey="date"
                      yAxisKey="score"
                      height={400}
                    />
                  )}
                </Box>
              </Paper>
            </Grid>

            {/* Correlation Matrix */}
            <Grid item xs={12}>
              <CorrelationMatrix
                symbols={[selectedSymbol, ...portfolioData.map(p => p.symbol)]}
                timeframe={timeframe}
              />
            </Grid>

            {/* News Feed */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Latest News
                  </Typography>
                  <NewsFeed symbol={selectedSymbol} />
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Portfolio Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Positions
              </Typography>
              <DataTable
                columns={portfolioColumns}
                data={portfolioData}
                defaultSortBy="symbol"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage; 