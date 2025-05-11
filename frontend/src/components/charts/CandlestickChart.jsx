import React from 'react';
import {
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Rectangle,
} from 'recharts';
import { Box, Typography, useTheme } from '@mui/material';

const CustomCandlestick = (props) => {
  const { x, y, width, height, low, high, open, close } = props;
  const isGrowing = open < close;
  const color = isGrowing ? '#2e7d32' : '#d32f2f';
  const wickY1 = Math.min(open, close);
  const wickY2 = Math.max(open, close);
  const bodyY = Math.min(open, close);
  const bodyHeight = Math.abs(close - open);

  return (
    <g>
      {/* Wick */}
      <line
        x1={x + width / 2}
        y1={y + height - (low - props.min) * props.scale}
        x2={x + width / 2}
        y2={y + height - (high - props.min) * props.scale}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body */}
      <Rectangle
        x={x}
        y={y + height - (bodyY + bodyHeight - props.min) * props.scale}
        width={width}
        height={bodyHeight * props.scale}
        fill={color}
        stroke={color}
      />
    </g>
  );
};

const CandlestickChart = ({
  data,
  title,
  height = 400,
  showLegend = true,
  showGrid = true,
  showTooltip = true,
}) => {
  const theme = useTheme();

  const min = Math.min(...data.map((d) => d.low));
  const max = Math.max(...data.map((d) => d.high));
  const scale = height / (max - min);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box
          sx={{
            backgroundColor: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
            p: 1,
            borderRadius: 1,
          }}
        >
          <Typography variant="body2">{`Date: ${label}`}</Typography>
          <Typography variant="body2">{`Open: ${data.open}`}</Typography>
          <Typography variant="body2">{`High: ${data.high}`}</Typography>
          <Typography variant="body2">{`Low: ${data.low}`}</Typography>
          <Typography variant="body2">{`Close: ${data.close}`}</Typography>
          <Typography variant="body2">{`Volume: ${data.volume}`}</Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Box sx={{ width: '100%', height }}>
      {title && (
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
      )}
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={theme.palette.divider}
            />
          )}
          <XAxis
            dataKey="date"
            stroke={theme.palette.text.secondary}
            tick={{ fill: theme.palette.text.secondary }}
          />
          <YAxis
            stroke={theme.palette.text.secondary}
            tick={{ fill: theme.palette.text.secondary }}
            domain={[min, max]}
          />
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && <Legend />}
          <CustomCandlestick
            dataKey="price"
            fill="#8884d8"
            min={min}
            scale={scale}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default CandlestickChart; 