import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { useWebSocket } from '../hooks/useWebSocket';
import LoadingSpinner from '../components/LoadingSpinner';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Alert,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { tradingAPI, marketAPI } from '../config/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const ASSETS = ['AAPL', 'TSLA', 'GOOG', 'AMZN', 'MSFT'];

const TradingPage = () => {
  const { user } = useAuth();
  const { showNotification } = useNotification();
  const [ticker, setTicker] = useState('AAPL');
  const [quantity, setQuantity] = useState(1);
  const [price, setPrice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [orderType, setOrderType] = useState('market');
  const [limitPrice, setLimitPrice] = useState('');
  const [priceHistory, setPriceHistory] = useState([]);
  const [signals, setSignals] = useState(null);
  const [stockData, setStockData] = useState(null);
  const { register, handleSubmit, formState: { errors }, watch } = useForm();
  const symbol = watch('symbol');

  // WebSocket connections
  const { ws: tradingWs } = useWebSocket('trading', ticker);

  const { execute: fetchStockData } = useApi(marketAPI.getStockData);
  const { execute: placeOrder } = useApi(tradingAPI.placeOrder);

  // Handle WebSocket messages
  useEffect(() => {
    if (tradingWs) {
      tradingWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'price_update') {
          setPrice(data.data.price);
          setPriceHistory(prev => {
            const newData = [...prev, { timestamp: new Date(), price: data.data.price }];
            return newData.slice(-30); // Keep last 30 data points
          });
        } else if (data.type === 'trading_signal') {
          setSignals(data.data);
        }
      };
    }
  }, [tradingWs]);

  useEffect(() => {
    const loadStockData = async () => {
      if (symbol) {
        try {
          const data = await fetchStockData(symbol);
          setStockData(data);
        } catch (error) {
          console.error('Failed to load stock data:', error);
          setStockData(null);
        }
      }
    };

    const debounceTimer = setTimeout(loadStockData, 500);
    return () => clearTimeout(debounceTimer);
  }, [symbol, fetchStockData]);

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    try {
      const [priceRes, signalsRes] = await Promise.all([
        axios.get(`/api/v1/trading/price/${ticker}`),
        axios.get(`/api/v1/technical/analyze/${ticker}`)
      ]);
      setPrice(priceRes.data.price);
      setSignals(signalsRes.data);
      setPriceHistory([{ timestamp: new Date(), price: priceRes.data.price }]);
    } catch (error) {
      showNotification('Failed to fetch trading data', 'error');
      setPrice(null);
      setSignals(null);
    }
    setLoading(false);
  }, [ticker, showNotification]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      await placeOrder({
        symbol: data.symbol,
        order_type: orderType,
        quantity: parseInt(data.quantity),
        price: orderType === 'limit' ? parseFloat(data.price) : undefined,
      });
      toast.success('Order placed successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !price) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Trading
      </Typography>

      <Grid container spacing={3}>
        {/* Stock Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Stock Information" />
            <Divider />
            <CardContent>
              {stockData ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {stockData.symbol}: ${stockData.price}
                  </Typography>
                  <Typography
                    variant="body1"
                    color={stockData.change >= 0 ? 'success.main' : 'error.main'}
                  >
                    {stockData.change > 0 ? '+' : ''}
                    {stockData.change}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Volume: {stockData.volume.toLocaleString()}
                  </Typography>
                </Box>
              ) : (
                <Typography>Enter a symbol to view stock information</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Trading Form */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Place Order
            </Typography>
            <Box component="form" onSubmit={handleSubmit(onSubmit)}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Symbol"
                    {...register('symbol', {
                      required: 'Symbol is required',
                      pattern: {
                        value: /^[A-Z]{1,5}$/,
                        message: 'Invalid symbol format',
                      },
                    })}
                    error={!!errors.symbol}
                    helperText={errors.symbol?.message}
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Order Type</InputLabel>
                    <Select
                      value={orderType}
                      label="Order Type"
                      onChange={(e) => setOrderType(e.target.value)}
                    >
                      <MenuItem value="market">Market</MenuItem>
                      <MenuItem value="limit">Limit</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {orderType === 'limit' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Limit Price"
                      type="number"
                      step="0.01"
                      {...register('price', {
                        required: 'Limit price is required',
                        min: {
                          value: 0.01,
                          message: 'Price must be greater than 0',
                        },
                      })}
                      error={!!errors.price}
                      helperText={errors.price?.message}
                    />
                  </Grid>
                )}

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Quantity"
                    type="number"
                    {...register('quantity', {
                      required: 'Quantity is required',
                      min: {
                        value: 1,
                        message: 'Quantity must be at least 1',
                      },
                    })}
                    error={!!errors.quantity}
                    helperText={errors.quantity?.message}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Place Order'}
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Trading</h2>
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Asset:</label>
              <select
                value={ticker}
                onChange={e => setTicker(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ASSETS.map(asset => (
                  <option key={asset} value={asset}>{asset}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="text-sm text-gray-500 mb-1">Current Price</div>
                <div className="text-3xl font-bold text-gray-900">
                  ${price?.toFixed(2) || 'Loading...'}
                </div>
              </div>

              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Order Type
                  </label>
                  <select
                    value={orderType}
                    onChange={e => setOrderType(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="market">Market</option>
                    <option value="limit">Limit</option>
                  </select>
                </div>

                {orderType === 'limit' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Limit Price
                    </label>
                    <input
                      type="number"
                      value={limitPrice}
                      onChange={e => setLimitPrice(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter limit price"
                      step="0.01"
                      min="0"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={e => setQuantity(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                  />
                </div>

                <div className="flex space-x-4">
                  <button
                    type="submit"
                    name="buy"
                    onClick={handleSubmit(onSubmit)}
                    disabled={loading}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
                  >
                    {loading ? <LoadingSpinner size="sm" /> : 'Buy'}
                  </button>
                  <button
                    type="submit"
                    name="sell"
                    onClick={handleSubmit(onSubmit)}
                    disabled={loading}
                    className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
                  >
                    {loading ? <LoadingSpinner size="sm" /> : 'Sell'}
                  </button>
                </div>
              </form>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Price History</h3>
              <div className="h-64">
                <Line
                  data={{
                    labels: priceHistory.map(p => p.timestamp.toLocaleTimeString()),
                    datasets: [
                      {
                        label: 'Price',
                        data: priceHistory.map(p => p.price),
                        borderColor: 'rgb(59,130,246)',
                        backgroundColor: 'rgba(59,130,246,0.2)',
                        tension: 0.4,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      title: { display: false },
                    },
                    scales: {
                      y: {
                        beginAtZero: false,
                        grid: {
                          color: 'rgba(0, 0, 0, 0.1)',
                        },
                      },
                      x: {
                        grid: {
                          display: false,
                        },
                      },
                    },
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {signals && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Trading Signals</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(signals.signals || {}).map(([key, val]) => (
                <div
                  key={key}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  <div className="font-medium text-gray-900 mb-2">{key}</div>
                  <div className="text-sm text-gray-600 mb-1">
                    Value: {typeof val.value === 'number' ? val.value.toFixed(2) : val.value}
                  </div>
                  <div className="text-sm">
                    Signal:{' '}
                    <span
                      className={`font-semibold ${
                        val.signal === 'buy'
                          ? 'text-green-600'
                          : val.signal === 'sell'
                          ? 'text-red-600'
                          : 'text-blue-600'
                      }`}
                    >
                      {val.signal.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Box>
  );
};

export default TradingPage; 