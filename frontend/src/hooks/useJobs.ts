import { useState, useCallback, useEffect, useRef } from 'react';
import { Job, JobListResponse } from '../types';
import { jobsApi } from '../api/client';

export function useJobs(autoRefresh = false, refreshInterval = 3000) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const fetchJobs = useCallback(async (pageNum = page) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response: JobListResponse = await jobsApi.list(pageNum, pageSize);
      setJobs(response.jobs);
      setTotal(response.total);
      setTotalPages(response.total_pages);
      setPage(response.page);
    } catch (err) {
      setError('Failed to fetch jobs');
      console.error('Error fetching jobs:', err);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize]);

  const refreshJob = useCallback(async (jobId: string): Promise<Job | null> => {
    try {
      const job = await jobsApi.get(jobId);
      setJobs(prevJobs => 
        prevJobs.map(j => j.id === jobId ? job : j)
      );
      return job;
    } catch (err) {
      console.error('Error refreshing job:', err);
      return null;
    }
  }, []);

  const deleteJob = useCallback(async (jobId: string) => {
    try {
      await jobsApi.delete(jobId);
      setJobs(prevJobs => prevJobs.filter(j => j.id !== jobId));
      setTotal(prev => prev - 1);
    } catch (err) {
      console.error('Error deleting job:', err);
      throw err;
    }
  }, []);

  // Auto-refresh for pending/processing jobs
  useEffect(() => {
    if (!autoRefresh) return;

    const hasActiveJobs = jobs.some(
      job => job.status === 'pending' || job.status === 'processing'
    );

    if (hasActiveJobs) {
      intervalRef.current = window.setInterval(() => {
        fetchJobs(page);
      }, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh, jobs, page, fetchJobs, refreshInterval]);

  // Initial fetch
  useEffect(() => {
    fetchJobs();
  }, []);

  return {
    jobs,
    total,
    page,
    pageSize,
    totalPages,
    isLoading,
    error,
    fetchJobs,
    refreshJob,
    deleteJob,
    setPage: (newPage: number) => {
      setPage(newPage);
      fetchJobs(newPage);
    },
  };
}

export function useJobPolling(jobId: string | null, interval = 2000) {
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const fetchJob = useCallback(async () => {
    if (!jobId) return;
    
    setIsLoading(true);
    try {
      const jobData = await jobsApi.get(jobId);
      setJob(jobData);
      setError(null);
      
      // Stop polling if job is completed or failed
      if (jobData.status === 'completed' || jobData.status === 'failed') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      setError('Failed to fetch job status');
      console.error('Error fetching job:', err);
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    // Initial fetch
    fetchJob();

    // Start polling
    intervalRef.current = window.setInterval(fetchJob, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, interval, fetchJob]);

  return { job, isLoading, error, refetch: fetchJob };
}
