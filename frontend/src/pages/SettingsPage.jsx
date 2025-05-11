import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
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
import { userAPI } from '../config/api';

const SettingsPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState(null);
  const { register, handleSubmit, formState: { errors }, reset } = useForm();

  const { execute: fetchProfile } = useApi(userAPI.getProfile);
  const { execute: updateProfile } = useApi(userAPI.updateProfile);
  const { execute: updateSettings } = useApi(userAPI.updateSettings);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const data = await fetchProfile();
        setSettings(data.settings);
        reset(data);
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    };

    loadSettings();
  }, [fetchProfile, reset]);

  const onSubmit = async (data) => {
    try {
      setIsLoading(true);
      await updateProfile({
        name: data.name,
        email: data.email,
      });
      await updateSettings({
        notifications: data.notifications,
        theme: data.theme,
        language: data.language,
      });
      toast.success('Settings updated successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        {/* Profile Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Profile Settings" />
            <Divider />
            <CardContent>
              <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Name"
                      {...register('name', {
                        required: 'Name is required',
                      })}
                      error={!!errors.name}
                      helperText={errors.name?.message}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Email"
                      type="email"
                      {...register('email', {
                        required: 'Email is required',
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: 'Invalid email address',
                        },
                      })}
                      error={!!errors.email}
                      helperText={errors.email?.message}
                    />
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Preferences */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Preferences" />
            <Divider />
            <CardContent>
              <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          {...register('notifications')}
                          defaultChecked={settings?.notifications}
                        />
                      }
                      label="Enable Notifications"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      select
                      label="Theme"
                      {...register('theme')}
                      defaultValue={settings?.theme || 'light'}
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="system">System</option>
                    </TextField>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      select
                      label="Language"
                      {...register('language')}
                      defaultValue={settings?.language || 'en'}
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                    </TextField>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleSubmit(onSubmit)}
              disabled={isLoading}
              sx={{ minWidth: 200 }}
            >
              {isLoading ? <CircularProgress size={24} /> : 'Save Changes'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SettingsPage; 