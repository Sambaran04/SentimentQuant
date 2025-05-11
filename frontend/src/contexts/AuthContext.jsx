import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import jwtDecode from 'jwt-decode';
import { authAPI } from '../config/api';
import { useNotification } from './NotificationContext';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const { showError } = useNotification();

  const refreshToken = useCallback(async () => {
    try {
      const response = await authAPI.refreshToken();
      const { token } = response.data;
      localStorage.setItem('token', token);
      const decodedToken = jwtDecode(token);
      setUser(decodedToken);
      setIsAuthenticated(true);
      return token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      logout();
      throw error;
    }
  }, []);

  const checkTokenExpiration = useCallback(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decodedToken = jwtDecode(token);
        const expirationTime = decodedToken.exp * 1000;
        const currentTime = Date.now();
        const timeUntilExpiration = expirationTime - currentTime;

        // If token expires in less than 5 minutes, refresh it
        if (timeUntilExpiration < 300000) {
          refreshToken();
        }
      } catch (error) {
        console.error('Error checking token expiration:', error);
        logout();
      }
    }
  }, [refreshToken]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decodedToken = jwtDecode(token);
        if (decodedToken.exp * 1000 > Date.now()) {
          setUser(decodedToken);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('token');
        }
      } catch (error) {
        console.error('Error decoding token:', error);
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  }, []);

  // Set up token refresh interval
  useEffect(() => {
    if (isAuthenticated) {
      const interval = setInterval(checkTokenExpiration, 60000); // Check every minute
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, checkTokenExpiration]);

  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials);
      const { token } = response.data;
      localStorage.setItem('token', token);
      const decodedToken = jwtDecode(token);
      setUser(decodedToken);
      setIsAuthenticated(true);
      return response;
    } catch (error) {
      showError(error.response?.data?.message || 'Login failed');
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      return response;
    } catch (error) {
      showError(error.response?.data?.message || 'Registration failed');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  };

  const forgotPassword = async (email) => {
    try {
      const response = await authAPI.forgotPassword(email);
      return response;
    } catch (error) {
      showError(error.response?.data?.message || 'Password reset request failed');
      throw error;
    }
  };

  const resetPassword = async (data) => {
    try {
      const response = await authAPI.resetPassword(data);
      return response;
    } catch (error) {
      showError(error.response?.data?.message || 'Password reset failed');
      throw error;
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext; 