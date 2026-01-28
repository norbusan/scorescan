import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, CheckCircle, XCircle, Shield, ShieldOff, Clock, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { adminApi } from '../api/client';
import { User, UserListResponse } from '../types';

export default function Admin() {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    superusers: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [processingUserId, setProcessingUserId] = useState<string | null>(null);

  // Redirect if not superuser
  useEffect(() => {
    if (currentUser && !currentUser.is_superuser) {
      toast.error('Access denied: Superuser privileges required');
      navigate('/dashboard');
    }
  }, [currentUser, navigate]);

  // Load users
  useEffect(() => {
    if (currentUser?.is_superuser) {
      loadUsers();
    }
  }, [currentUser]);

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      const data: UserListResponse = await adminApi.listAllUsers();
      setUsers(data.users);
      setStats({
        total: data.total,
        pending: data.pending,
        approved: data.approved,
        superusers: data.superusers,
      });
    } catch (error) {
      toast.error('Failed to load users');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (userId: string, email: string) => {
    try {
      setProcessingUserId(userId);
      await adminApi.approveUser(userId);
      toast.success(`Approved ${email}`);
      await loadUsers();
    } catch (error) {
      toast.error('Failed to approve user');
      console.error(error);
    } finally {
      setProcessingUserId(null);
    }
  };

  const handleReject = async (userId: string, email: string) => {
    if (!window.confirm(`Are you sure you want to reject and delete ${email}?`)) {
      return;
    }

    try {
      setProcessingUserId(userId);
      await adminApi.rejectUser(userId);
      toast.success(`Rejected ${email}`);
      await loadUsers();
    } catch (error) {
      toast.error('Failed to reject user');
      console.error(error);
    } finally {
      setProcessingUserId(null);
    }
  };

  const handleMakeSuperuser = async (userId: string, email: string) => {
    if (!window.confirm(`Grant superuser privileges to ${email}?`)) {
      return;
    }

    try {
      setProcessingUserId(userId);
      await adminApi.makeSuperuser(userId);
      toast.success(`${email} is now a superuser`);
      await loadUsers();
    } catch (error) {
      toast.error('Failed to grant superuser privileges');
      console.error(error);
    } finally {
      setProcessingUserId(null);
    }
  };

  const handleRevokeSuperuser = async (userId: string, email: string) => {
    if (!window.confirm(`Revoke superuser privileges from ${email}?`)) {
      return;
    }

    try {
      setProcessingUserId(userId);
      await adminApi.revokeSuperuser(userId);
      toast.success(`Revoked superuser privileges from ${email}`);
      await loadUsers();
    } catch (error) {
      toast.error('Failed to revoke superuser privileges');
      console.error(error);
    } finally {
      setProcessingUserId(null);
    }
  };

  if (!currentUser?.is_superuser) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Shield className="h-8 w-8 text-primary-600" />
          User Management
        </h1>
        <p className="mt-2 text-gray-600">
          Approve new users and manage superuser privileges
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <Users className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Approval</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Approved</p>
              <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Superusers</p>
              <p className="text-2xl font-bold text-primary-600">{stats.superusers}</p>
            </div>
            <Shield className="h-8 w-8 text-primary-400" />
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">All Users</h2>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Users className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {user.email}
                            {user.id === currentUser.id && (
                              <span className="ml-2 text-xs text-gray-500">(You)</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.is_approved ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Approved
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          <Clock className="h-3 w-3 mr-1" />
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.is_superuser ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                          <Shield className="h-3 w-3 mr-1" />
                          Superuser
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">User</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        {!user.is_approved && (
                          <>
                            <button
                              onClick={() => handleApprove(user.id, user.email)}
                              disabled={processingUserId === user.id}
                              className="text-green-600 hover:text-green-900 disabled:opacity-50"
                              title="Approve user"
                            >
                              {processingUserId === user.id ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                              ) : (
                                <CheckCircle className="h-5 w-5" />
                              )}
                            </button>
                            <button
                              onClick={() => handleReject(user.id, user.email)}
                              disabled={processingUserId === user.id}
                              className="text-red-600 hover:text-red-900 disabled:opacity-50"
                              title="Reject user"
                            >
                              <XCircle className="h-5 w-5" />
                            </button>
                          </>
                        )}
                        
                        {user.is_approved && user.id !== currentUser.id && (
                          <>
                            {user.is_superuser ? (
                              <button
                                onClick={() => handleRevokeSuperuser(user.id, user.email)}
                                disabled={processingUserId === user.id}
                                className="text-orange-600 hover:text-orange-900 disabled:opacity-50"
                                title="Revoke superuser"
                              >
                                {processingUserId === user.id ? (
                                  <Loader2 className="h-5 w-5 animate-spin" />
                                ) : (
                                  <ShieldOff className="h-5 w-5" />
                                )}
                              </button>
                            ) : (
                              <button
                                onClick={() => handleMakeSuperuser(user.id, user.email)}
                                disabled={processingUserId === user.id}
                                className="text-primary-600 hover:text-primary-900 disabled:opacity-50"
                                title="Make superuser"
                              >
                                {processingUserId === user.id ? (
                                  <Loader2 className="h-5 w-5 animate-spin" />
                                ) : (
                                  <Shield className="h-5 w-5" />
                                )}
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
