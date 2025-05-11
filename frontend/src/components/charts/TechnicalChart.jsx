import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  Draw as DrawIcon,
  ShowChart as ShowChartIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const TechnicalChart = ({
  data,
  title,
  height = 400,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
}) => {
  const [drawingTool, setDrawingTool] = useState(null);
  const [indicators, setIndicators] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleIndicatorAdd = (indicator) => {
    setIndicators((prev) => [...prev, indicator]);
    handleMenuClose();
  };

  const calculateMA = (data, period) => {
    return data.map((item, index) => {
      if (index < period - 1) return null;
      const sum = data
        .slice(index - period + 1, index + 1)
        .reduce((acc, curr) => acc + curr.close, 0);
      return sum / period;
    });
  };

  const calculateRSI = (data, period = 14) => {
    const changes = data.map((item, index) => {
      if (index === 0) return 0;
      return item.close - data[index - 1].close;
    });

    const gains = changes.map((change) => (change > 0 ? change : 0));
    const losses = changes.map((change) => (change < 0 ? -change : 0));

    const avgGain = gains.slice(period).map((_, index) => {
      const sum = gains.slice(index, index + period).reduce((a, b) => a + b, 0);
      return sum / period;
    });

    const avgLoss = losses.slice(period).map((_, index) => {
      const sum = losses.slice(index, index + period).reduce((a, b) => a + b, 0);
      return sum / period;
    });

    const rsi = avgGain.map((gain, index) => {
      const loss = avgLoss[index];
      if (loss === 0) return 100;
      const rs = gain / loss;
      return 100 - 100 / (1 + rs);
    });

    return Array(period).fill(null).concat(rsi);
  };

  const renderIndicators = () => {
    return indicators.map((indicator, index) => {
      switch (indicator) {
        case 'MA20':
          return (
            <Line
              key={`ma20-${index}`}
              type="monotone"
              dataKey="ma20"
              stroke="#2196f3"
              dot={false}
              name="MA20"
            />
          );
        case 'MA50':
          return (
            <Line
              key={`ma50-${index}`}
              type="monotone"
              dataKey="ma50"
              stroke="#f50057"
              dot={false}
              name="MA50"
            />
          );
        case 'RSI':
          return (
            <Line
              key={`rsi-${index}`}
              type="monotone"
              dataKey="rsi"
              stroke="#4caf50"
              dot={false}
              name="RSI"
            />
          );
        default:
          return null;
      }
    });
  };

  const processedData = data.map((item, index) => {
    const ma20 = calculateMA(data, 20)[index];
    const ma50 = calculateMA(data, 50)[index];
    const rsi = calculateRSI(data)[index];

    return {
      ...item,
      ma20,
      ma50,
      rsi,
    };
  });

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Box>
          <Tooltip title="Drawing Tools">
            <IconButton
              color={drawingTool ? 'primary' : 'default'}
              onClick={() => setDrawingTool(drawingTool ? null : 'line')}
            >
              <DrawIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Indicators">
            <IconButton onClick={handleMenuClick}>
              <ShowChartIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={processedData}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis dataKey="date" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          {showTooltip && (
            <RechartsTooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <Paper sx={{ p: 1 }}>
                      <Typography variant="body2">{label}</Typography>
                      {payload.map((entry, index) => (
                        <Typography
                          key={index}
                          variant="body2"
                          sx={{ color: entry.color }}
                        >
                          {entry.name}: {entry.value.toFixed(2)}
                        </Typography>
                      ))}
                    </Paper>
                  );
                }
                return null;
              }}
            />
          )}
          {showLegend && <Legend />}
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="close"
            stroke="#000"
            dot={false}
            name="Price"
          />
          {renderIndicators()}
        </ComposedChart>
      </ResponsiveContainer>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleIndicatorAdd('MA20')}>
          Moving Average (20)
        </MenuItem>
        <MenuItem onClick={() => handleIndicatorAdd('MA50')}>
          Moving Average (50)
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => handleIndicatorAdd('RSI')}>
          Relative Strength Index
        </MenuItem>
      </Menu>
    </Paper>
  );
};

export default TechnicalChart; 