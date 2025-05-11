import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Button,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { tradingAPI } from '../config/api';

const PortfolioPage = () => {
  const navigate = useNavigate();
  const [portfolioData, setPortfolioData] = useState(null);
  const { execute: fetchPortfolio, loading } = useApi(tradingAPI.getPortfolio);

  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        const data = await fetchPortfolio();
        setPortfolioData(data);
      } catch (error) {
        console.error('Failed to load portfolio:', error);
      }
    };

    loadPortfolio();
  }, [fetchPortfolio]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Portfolio</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/trading')}
        >
          New Trade
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Portfolio Summary */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Portfolio Summary" />
            <Divider />
            <CardContent>
              {portfolioData ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="h6">Total Value</Typography>
                    <Typography variant="h4" color="primary">
                      ${portfolioData.total_value.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="h6">Daily Change</Typography>
                    <Typography
                      variant="h4"
                      color={portfolioData.daily_change >= 0 ? 'success.main' : 'error.main'}
                    >
                      {portfolioData.daily_change > 0 ? '+' : ''}
                      {portfolioData.daily_change}%
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="h6">Total Profit/Loss</Typography>
                    <Typography
                      variant="h4"
                      color={portfolioData.total_pl >= 0 ? 'success.main' : 'error.main'}
                    >
                      ${portfolioData.total_pl.toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
              ) : (
                <Typography>No portfolio data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Holdings Table */}
        <Grid item xs={12}>
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell align="right">Shares</TableCell>
                    <TableCell align="right">Avg. Price</TableCell>
                    <TableCell align="right">Current Price</TableCell>
                    <TableCell align="right">Market Value</TableCell>
                    <TableCell align="right">Profit/Loss</TableCell>
                    <TableCell align="right">% Change</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {portfolioData?.holdings.map((holding) => (
                    <TableRow key={holding.symbol}>
                      <TableCell component="th" scope="row">
                        {holding.symbol}
                      </TableCell>
                      <TableCell align="right">{holding.shares}</TableCell>
                      <TableCell align="right">
                        ${holding.average_price.toFixed(2)}
                      </TableCell>
                      <TableCell align="right">
                        ${holding.current_price.toFixed(2)}
                      </TableCell>
                      <TableCell align="right">
                        ${holding.market_value.toLocaleString()}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{
                          color: holding.profit_loss >= 0 ? 'success.main' : 'error.main',
                        }}
                      >
                        ${holding.profit_loss.toLocaleString()}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{
                          color: holding.percent_change >= 0 ? 'success.main' : 'error.main',
                        }}
                      >
                        {holding.percent_change > 0 ? '+' : ''}
                        {holding.percent_change}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioPage; 