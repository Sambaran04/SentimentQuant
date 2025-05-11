import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import axios from 'axios';

const Watchlist = ({ onSymbolSelect }) => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/api/v1/watchlist');
      setWatchlist(response.data);
    } catch (err) {
      setError('Failed to fetch watchlist');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (symbol) => {
    try {
      await axios.delete(`/api/v1/watchlist/${symbol}`);
      setWatchlist((prev) => prev.filter((item) => item.symbol !== symbol));
    } catch (err) {
      setError('Failed to remove from watchlist');
    }
  };

  const getPriceChangeColor = (change) => {
    return change >= 0 ? 'success.main' : 'error.main';
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
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Watchlist</Typography>
          <Tooltip title="Add to Watchlist">
            <IconButton size="small">
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <List>
          {watchlist.map((item) => (
            <ListItem
              key={item.symbol}
              button
              onClick={() => onSymbolSelect(item.symbol)}
              sx={{
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1">{item.symbol}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.name}
                    </Typography>
                  </Box>
                }
                secondary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="body2"
                      color={getPriceChangeColor(item.priceChange)}
                      sx={{ display: 'flex', alignItems: 'center' }}
                    >
                      {item.priceChange >= 0 ? (
                        <TrendingUpIcon fontSize="small" />
                      ) : (
                        <TrendingDownIcon fontSize="small" />
                      )}
                      {item.priceChange.toFixed(2)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ${item.price.toFixed(2)}
                    </Typography>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={item.sentiment}
                    size="small"
                    color={
                      item.sentiment === 'positive'
                        ? 'success'
                        : item.sentiment === 'negative'
                        ? 'error'
                        : 'default'
                    }
                  />
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemove(item.symbol);
                    }}
                  >
                    <RemoveIcon />
                  </IconButton>
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default Watchlist; 