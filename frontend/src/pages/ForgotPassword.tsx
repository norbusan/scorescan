import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Music, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api/client';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      toast.error('Please enter your email address');
      return;
    }

    setIsSubmitting(true);

    try {
      await api.post('/auth/password-reset/request', { email });
      setSubmitted(true);
      toast.success('Password reset instructions sent to your email');
    } catch (error: any) {
      console.error('Password reset request error:', error);
      // Don't show specific error for security reasons
      setSubmitted(true);
      toast.success('If the email exists, reset instructions have been sent');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Music className="mx-auto h-12 w-12 text-primary-600" />
            <h1 className="mt-4 text-3xl font-bold text-gray-900">
              Check your email
            </h1>
            <p className="mt-2 text-gray-600">
              If an account exists for <strong>{email}</strong>, you will receive password reset instructions.
            </p>
          </div>

          <div className="card p-6 sm:p-8">
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                <p className="font-medium mb-1">Next steps:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Check your email inbox</li>
                  <li>Click the reset link in the email</li>
                  <li>Set your new password</li>
                </ul>
              </div>

              <div className="text-sm text-gray-600">
                <p>Didn't receive the email? Check your spam folder or try again.</p>
              </div>

              <Link
                to="/login"
                className="btn-secondary w-full flex items-center justify-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to login
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Music className="mx-auto h-12 w-12 text-primary-600" />
          <h1 className="mt-4 text-3xl font-bold text-gray-900">
            Forgot your password?
          </h1>
          <p className="mt-2 text-gray-600">
            No worries! Enter your email and we'll send you reset instructions.
          </p>
        </div>

        <div className="card p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="label">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                disabled={isSubmitting}
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full"
            >
              {isSubmitting ? 'Sending...' : 'Send reset instructions'}
            </button>

            <div className="text-center">
              <Link
                to="/login"
                className="text-sm text-gray-600 hover:text-primary-600 inline-flex items-center gap-1"
              >
                <ArrowLeft className="h-3 w-3" />
                Back to login
              </Link>
            </div>
          </form>
        </div>

        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
