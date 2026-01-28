// User types
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_approved: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

// Auth types
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;  // email (OAuth2 form uses username field)
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

// Job types
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Job {
  id: string;
  status: JobStatus;
  progress: number;
  original_filename: string;
  transpose_semitones: number | null;
  transpose_from_key: string | null;
  transpose_to_key: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  has_pdf: boolean;
  has_musicxml: boolean;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Transpose options
export interface TransposeOptions {
  semitones?: number;
  from_key?: string;
  to_key?: string;
}

// API Error
export interface APIError {
  detail: string;
}

// Admin types
export interface UserListResponse {
  users: User[];
  total: number;
  pending: number;
  approved: number;
  superusers: number;
}

// Keys for transposition
export const MUSICAL_KEYS = [
  'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 
  'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B',
  'Cm', 'C#m', 'Dm', 'D#m', 'Ebm', 'Em', 'Fm',
  'F#m', 'Gm', 'G#m', 'Abm', 'Am', 'A#m', 'Bbm', 'Bm'
] as const;

export type MusicalKey = typeof MUSICAL_KEYS[number];
