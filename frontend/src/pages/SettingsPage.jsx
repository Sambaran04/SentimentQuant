import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import LoadingSpinner from '../components/LoadingSpinner';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { showNotification } = useNotification();
  const [profile, setProfile] = useState(null);
  const [email, setEmail] = useState('');
  const [strategyConfig, setStrategyConfig] = useState('{}');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/api/v1/users/me');
        setProfile(res.data);
        setEmail(res.data.email || '');
        setStrategyConfig(JSON.stringify(res.data.strategy_config || {}, null, 2));
      } catch (error) {
        showNotification('Failed to fetch profile', 'error');
        setProfile(null);
      }
      setLoading(false);
    };
    fetchProfile();
  }, [showNotification]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let parsedConfig;
      try {
        parsedConfig = JSON.parse(strategyConfig);
      } catch (error) {
        showNotification('Invalid JSON in strategy config', 'error');
        setSubmitting(false);
        return;
      }

      const res = await axios.put('/api/v1/users/me', {
        username: profile.username,
        email,
        is_active: profile.is_active,
        is_superuser: profile.is_superuser,
        strategy_config: parsedConfig
      });
      showNotification('Profile updated successfully!', 'success');
    } catch (error) {
      showNotification('Failed to update profile', 'error');
    }
    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h2>
        {profile ? (
          <form onSubmit={handleUpdate} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
              <input
                type="text"
                value={profile.username}
                disabled
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-gray-50 text-gray-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Strategy Config (JSON)</label>
              <textarea
                value={strategyConfig}
                onChange={e => setStrategyConfig(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="8"
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className={`px-6 py-2 rounded-md text-white font-medium ${
                  submitting
                    ? 'bg-blue-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {submitting ? (
                  <div className="flex items-center">
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Updating...</span>
                  </div>
                ) : (
                  'Update Profile'
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="text-center py-8 text-gray-500">
            Failed to load profile data
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Telegram Integration</h2>
        <div className="text-center py-8 text-gray-500">
          Coming soon: Link your Telegram for trade alerts!
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={logout}
          className="px-6 py-2 rounded-md text-white font-medium bg-red-600 hover:bg-red-700"
        >
          Logout
        </button>
      </div>
    </div>
  );
} 