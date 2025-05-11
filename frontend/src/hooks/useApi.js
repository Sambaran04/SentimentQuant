import { useState, useCallback } from 'react';
import { useNotification } from '../contexts/NotificationContext';

const useApi = (apiFunction) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { showError } = useNotification();

  const execute = useCallback(
    async (...args) => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiFunction(...args);
        setData(response.data);
        return response.data;
      } catch (err) {
        const errorMessage = err.response?.data?.message || 'An error occurred';
        setError(errorMessage);
        showError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, showError]
  );

  return {
    data,
    loading,
    error,
    execute,
  };
};

export default useApi; 