import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Music } from 'lucide-react';
import LoginForm from '../components/Auth/LoginForm';

export default function Login() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Music className="mx-auto h-12 w-12 text-primary-600" />
          <h1 className="mt-4 text-3xl font-bold text-gray-900">
            Welcome back
          </h1>
          <p className="mt-2 text-gray-600">
            Sign in to continue to ScoreScan
          </p>
        </div>

        <div className="card p-6 sm:p-8">
          <LoginForm onSuccess={() => navigate('/dashboard')} />
        </div>
      </div>
    </div>
  );
}
