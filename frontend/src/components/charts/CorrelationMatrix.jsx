import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import axios from 'axios';

const CorrelationMatrix = ({ symbols, timeframe = '1m' }) => {
  const [correlations, setCorrelations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCorrelations = async () => {
      if (!symbols || symbols.length === 0) return;

      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`/api/v1/correlation?symbols=${symbols.join(',')}&timeframe=${timeframe}`);
        setCorrelations(response.data);
      } catch (err) {
        setError('Failed to fetch correlation data');
      } finally {
        setLoading(false);
      }
    };

    fetchCorrelations();
  }, [symbols, timeframe]);

  const getCorrelationColor = (value) => {
    const absValue = Math.abs(value);
    if (absValue < 0.3) return '#e0e0e0';
    if (absValue < 0.5) return value > 0 ? '#90caf9' : '#ef9a9a';
    if (absValue < 0.7) return value > 0 ? '#42a5f5' : '#e57373';
    return value > 0 ? '#1976d2' : '#d32f2f';
  };

  if (loading) {
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
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Correlation Matrix
      </Typography>
      <Box sx={{ overflowX: 'auto' }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: `auto repeat(${symbols.length}, 1fr)`,
            gap: 1,
            minWidth: 'max-content',
          }}
        >
          {/* Header row */}
          <Box sx={{ p: 1 }} />
          {symbols.map((symbol) => (
            <Box
              key={symbol}
              sx={{
                p: 1,
                textAlign: 'center',
                fontWeight: 'bold',
                borderBottom: '1px solid',
                borderColor: 'divider',
              }}
            >
              {symbol}
            </Box>
          ))}

          {/* Matrix cells */}
          {symbols.map((symbol1, i) => (
            <React.Fragment key={symbol1}>
              <Box
                sx={{
                  p: 1,
                  textAlign: 'right',
                  fontWeight: 'bold',
                  borderRight: '1px solid',
                  borderColor: 'divider',
                }}
              >
                {symbol1}
              </Box>
              {symbols.map((symbol2, j) => {
                const correlation = correlations[i]?.[j] || 0;
                return (
                  <Tooltip
                    key={`${symbol1}-${symbol2}`}
                    title={`${symbol1} vs ${symbol2}: ${correlation.toFixed(2)}`}
                  >
                    <Box
                      sx={{
                        p: 1,
                        textAlign: 'center',
                        backgroundColor: getCorrelationColor(correlation),
                        color: Math.abs(correlation) > 0.7 ? 'white' : 'inherit',
                        cursor: 'pointer',
                        '&:hover': {
                          opacity: 0.8,
                        },
                      }}
                    >
                      {correlation.toFixed(2)}
                    </Box>
                  </Tooltip>
                );
              })}
            </React.Fragment>
          ))}
        </Box>
      </Box>
    </Paper>
  );
};

export default CorrelationMatrix; 