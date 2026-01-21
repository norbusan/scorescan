import React from 'react';
import { FileText, Download, Trash2, Music, ChevronLeft, ChevronRight } from 'lucide-react';
import { Job } from '../../types';
import JobStatusBadge, { JobProgress } from './JobStatus';
import { jobsApi } from '../../api/client';
import toast from 'react-hot-toast';

interface JobListProps {
  jobs: Job[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onDelete: (jobId: string) => Promise<void>;
  onRefresh: () => void;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function JobCard({ job, onDelete }: { job: Job; onDelete: () => void }) {
  const handleDownloadPdf = async () => {
    try {
      // Create a hidden link and trigger download
      const link = document.createElement('a');
      link.href = jobsApi.downloadPdf(job.id);
      link.download = `${job.original_filename.replace(/\.[^/.]+$/, '')}_processed.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      toast.error('Failed to download PDF');
    }
  };

  const handleDownloadMusicXml = async () => {
    try {
      const link = document.createElement('a');
      link.href = jobsApi.downloadMusicXml(job.id);
      link.download = `${job.original_filename.replace(/\.[^/.]+$/, '')}.musicxml`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      toast.error('Failed to download MusicXML');
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await onDelete();
        toast.success('Job deleted');
      } catch (err) {
        toast.error('Failed to delete job');
      }
    }
  };

  const getTransposeInfo = () => {
    if (job.transpose_semitones) {
      const sign = job.transpose_semitones > 0 ? '+' : '';
      return `${sign}${job.transpose_semitones} semitones`;
    }
    if (job.transpose_from_key && job.transpose_to_key) {
      return `${job.transpose_from_key} to ${job.transpose_to_key}`;
    }
    return null;
  };

  const transposeInfo = getTransposeInfo();

  return (
    <div className="card p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        {/* Left side - Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-gray-100 rounded-lg shrink-0">
              <FileText className="h-5 w-5 text-gray-600" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-medium text-gray-900 truncate">
                {job.original_filename}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {formatDate(job.created_at)}
              </p>
              {transposeInfo && (
                <div className="flex items-center space-x-1 mt-2 text-sm text-primary-600">
                  <Music className="h-4 w-4" />
                  <span>Transposed: {transposeInfo}</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Status and progress */}
          <div className="mt-4 space-y-2">
            <JobStatusBadge job={job} />
            <JobProgress job={job} />
            {job.error_message && (
              <p className="text-sm text-red-600 mt-2">{job.error_message}</p>
            )}
          </div>
        </div>

        {/* Right side - Actions */}
        <div className="flex sm:flex-col items-center sm:items-end gap-2">
          {job.status === 'completed' && (
            <>
              <button
                onClick={handleDownloadPdf}
                className="btn btn-primary text-sm"
              >
                <Download className="h-4 w-4 mr-1" />
                PDF
              </button>
              {job.has_musicxml && (
                <button
                  onClick={handleDownloadMusicXml}
                  className="btn btn-secondary text-sm"
                >
                  <Download className="h-4 w-4 mr-1" />
                  MusicXML
                </button>
              )}
            </>
          )}
          <button
            onClick={handleDelete}
            className="btn text-red-600 hover:bg-red-50 text-sm"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function JobList({
  jobs,
  page,
  totalPages,
  onPageChange,
  onDelete,
  onRefresh,
}: JobListProps) {
  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">No jobs yet</h3>
        <p className="mt-2 text-gray-500">
          Upload a music score to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Job cards */}
      <div className="space-y-4">
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onDelete={() => onDelete(job.id)}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-4 pt-4">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="btn btn-secondary disabled:opacity-50"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="btn btn-secondary disabled:opacity-50"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}
