import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Link,
  Chip,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import axios from 'axios';

const NewsFeed = ({ symbol }) => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedItems, setExpandedItems] = useState({});

  useEffect(() => {
    const fetchNews = async () => {
      if (!symbol) return;

      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`/api/v1/news/${symbol}`);
        setNews(response.data);
      } catch (err) {
        setError('Failed to fetch news');
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, [symbol]);

  const handleExpandClick = (id) => {
    setExpandedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      case 'neutral':
        return 'info';
      default:
        return 'default';
    }
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
    <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
      {news.map((item) => (
        <Card key={item.id} sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  <Link href={item.url} target="_blank" rel="noopener noreferrer">
                    {item.title}
                  </Link>
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {new Date(item.published_at).toLocaleString()}
                </Typography>
                <Box sx={{ mt: 1, mb: 1 }}>
                  <Chip
                    label={item.source}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  {item.sentiment && (
                    <Chip
                      label={item.sentiment}
                      size="small"
                      color={getSentimentColor(item.sentiment)}
                    />
                  )}
                </Box>
              </Box>
              <IconButton
                onClick={() => handleExpandClick(item.id)}
                sx={{
                  transform: expandedItems[item.id] ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
              >
                {expandedItems[item.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expandedItems[item.id]}>
              <Typography variant="body2" sx={{ mt: 2 }}>
                {item.summary}
              </Typography>
              {item.keywords && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Keywords:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {item.keywords.map((keyword, index) => (
                      <Chip
                        key={index}
                        label={keyword}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Collapse>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default NewsFeed; 