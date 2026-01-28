import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, Lock, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api/client';

export default function Settings() {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [changeSuccess, setChangeSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (currentPassword === newPassword) {
      toast.error('New password must be different from current password');
      return;
    }

    setIsSubmitting(true);
    setChangeSuccess(false);

    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      toast.success('Password changed successfully!');
      setChangeSuccess(true);
      
      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

      // Reset success message after 5 seconds
      setTimeout(() => {
        setChangeSuccess(false);
      }, 5000);
    } catch (error: any) {
      console.error('Change password error:', error);
      const message = error.response?.data?.detail || 'Failed to change password. Please check your current password.';
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setChangeSuccess(false);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Account Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage your account preferences and security settings
        </p>
      </div>

      {/* Account Information */}
      <div className="card mb-6">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Account Information
          </h2>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-500">Email</label>
              <p className="text-gray-900">{user?.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Account Type</label>
              <p className="text-gray-900">
                {user?.is_superuser ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    Administrator
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    Standard User
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="card">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Lock className="h-6 w-6 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Change Password
            </h2>
          </div>

          {changeSuccess && (
            <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-green-900">Password changed successfully!</p>
                <p className="text-sm text-green-700 mt-1">
                  Your password has been updated. Use your new password on your next login.
                </p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Current Password */}
            <div>
              <label htmlFor="currentPassword" className="label">
                Current Password
              </label>
              <div className="relative">
                <input
                  id="currentPassword"
                  type={showCurrentPassword ? 'text' : 'password'}
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Enter current password"
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  tabIndex={-1}
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div>
              <label htmlFor="newPassword" className="label">
                New Password
              </label>
              <div className="relative">
                <input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Enter new password"
                  disabled={isSubmitting}
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  tabIndex={-1}
                >
                  {showNewPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Must be at least 8 characters
              </p>
            </div>

            {/* Confirm New Password */}
            <div>
              <label htmlFor="confirmPassword" className="label">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Confirm new password"
                  disabled={isSubmitting}
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  tabIndex={-1}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Password Match Indicator */}
            {newPassword && confirmPassword && (
              <div className="text-sm">
                {newPassword === confirmPassword ? (
                  <p className="text-green-600 flex items-center gap-1">
                    <CheckCircle className="h-4 w-4" />
                    Passwords match
                  </p>
                ) : (
                  <p className="text-red-600">
                    Passwords do not match
                  </p>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={isSubmitting || newPassword !== confirmPassword || !currentPassword}
                className="btn-primary flex-1"
              >
                {isSubmitting ? 'Changing Password...' : 'Change Password'}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                disabled={isSubmitting}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Security Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">Password Security Tips</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Use at least 8 characters with a mix of letters, numbers, and symbols</li>
          <li>Avoid using common words or personal information</li>
          <li>Don't reuse passwords from other accounts</li>
          <li>Consider using a password manager</li>
        </ul>
      </div>
    </div>
  );
}
