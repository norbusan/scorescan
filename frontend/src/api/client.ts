import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { AuthTokens, User, Job, JobListResponse, RegisterData, APIError, UserListResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token storage
const TOKEN_KEY = 'scorescan_tokens';

export const getStoredTokens = (): AuthTokens | null => {
  const stored = localStorage.getItem(TOKEN_KEY);
  return stored ? JSON.parse(stored) : null;
};

export const setStoredTokens = (tokens: AuthTokens): void => {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
};

export const clearStoredTokens = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const tokens = getStoredTokens();
    if (tokens?.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // If 401 and not already retrying, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const tokens = getStoredTokens();
      if (tokens?.refresh_token) {
        try {
          const response = await axios.post<AuthTokens>(`${API_BASE_URL}/api/auth/refresh`, {
            refresh_token: tokens.refresh_token,
          });
          
          setStoredTokens(response.data);
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api(originalRequest);
        } catch {
          // Refresh failed, clear tokens and redirect to login
          clearStoredTokens();
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },
  
  login: async (email: string, password: string): Promise<AuthTokens> => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post<AuthTokens>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    
    setStoredTokens(response.data);
    return response.data;
  },
  
  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } finally {
      clearStoredTokens();
    }
  },
  
  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    setStoredTokens(response.data);
    return response.data;
  },
};

// Users API
export const usersApi = {
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/users/me');
    return response.data;
  },
};

// Jobs API
export const jobsApi = {
  create: async (
    file: File,
    transposeOptions?: {
      semitones?: number;
      fromKey?: string;
      toKey?: string;
    }
  ): Promise<Job> => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (transposeOptions?.semitones !== undefined) {
      formData.append('transpose_semitones', transposeOptions.semitones.toString());
    }
    if (transposeOptions?.fromKey) {
      formData.append('transpose_from_key', transposeOptions.fromKey);
    }
    if (transposeOptions?.toKey) {
      formData.append('transpose_to_key', transposeOptions.toKey);
    }
    
    const response = await api.post<Job>('/jobs', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  list: async (page = 1, pageSize = 10): Promise<JobListResponse> => {
    const response = await api.get<JobListResponse>('/jobs', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
  
  get: async (jobId: string): Promise<Job> => {
    const response = await api.get<Job>(`/jobs/${jobId}`);
    return response.data;
  },
  
  delete: async (jobId: string): Promise<void> => {
    await api.delete(`/jobs/${jobId}`);
  },
  
  downloadPdf: (jobId: string): string => {
    const tokens = getStoredTokens();
    return `${API_BASE_URL}/api/jobs/${jobId}/download/pdf?token=${tokens?.access_token || ''}`;
  },
  
  downloadMusicXml: (jobId: string): string => {
    const tokens = getStoredTokens();
    return `${API_BASE_URL}/api/jobs/${jobId}/download/musicxml?token=${tokens?.access_token || ''}`;
  },
};

// Admin API (requires superuser)
export const adminApi = {
  listAllUsers: async (): Promise<UserListResponse> => {
    const response = await api.get<UserListResponse>('/admin/users');
    return response.data;
  },
  
  listPendingUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/admin/users/pending');
    return response.data;
  },
  
  approveUser: async (userId: string): Promise<void> => {
    await api.post(`/admin/users/${userId}/approve`);
  },
  
  rejectUser: async (userId: string): Promise<void> => {
    await api.post(`/admin/users/${userId}/reject`);
  },
  
  makeSuperuser: async (userId: string): Promise<void> => {
    await api.post(`/admin/users/${userId}/make-superuser`);
  },
  
  revokeSuperuser: async (userId: string): Promise<void> => {
    await api.delete(`/admin/users/${userId}/superuser`);
  },
};

export default api;
