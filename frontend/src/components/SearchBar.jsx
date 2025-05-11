import React, { useState, useEffect } from 'react';
import {
  Autocomplete,
  TextField,
  CircularProgress,
  Box,
  Paper,
  Typography,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';

const SearchBar = ({ onSelect, initialValue = '' }) => {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState(initialValue);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    const fetchSymbols = async (query) => {
      if (!query || query.length < 2) {
        setOptions([]);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`/api/v1/stocks/search?query=${query}`);
        if (active) {
          setOptions(response.data);
        }
      } catch (err) {
        if (active) {
          setError('Failed to fetch stock symbols');
          setOptions([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    const timeoutId = setTimeout(() => {
      fetchSymbols(inputValue);
    }, 300);

    return () => {
      active = false;
      clearTimeout(timeoutId);
    };
  }, [inputValue]);

  return (
    <Autocomplete
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      inputValue={inputValue}
      onInputChange={(event, newInputValue) => {
        setInputValue(newInputValue);
      }}
      onChange={(event, newValue) => {
        if (newValue) {
          onSelect(newValue);
        }
      }}
      options={options}
      loading={loading}
      getOptionLabel={(option) => 
        typeof option === 'string' ? option : `${option.symbol} - ${option.name}`
      }
      renderOption={(props, option) => (
        <Box component="li" {...props}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="body1">
              {option.symbol}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {option.name}
            </Typography>
          </Box>
        </Box>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Search Stocks"
          variant="outlined"
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <SearchIcon sx={{ color: 'action.active', mr: 1 }} />
            ),
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      PaperComponent={({ children }) => (
        <Paper
          elevation={3}
          sx={{
            mt: 1,
            '& .MuiAutocomplete-listbox': {
              p: 0,
            },
          }}
        >
          {children}
        </Paper>
      )}
      sx={{
        width: '100%',
        '& .MuiOutlinedInput-root': {
          backgroundColor: 'background.paper',
        },
      }}
    />
  );
};

export default SearchBar; 