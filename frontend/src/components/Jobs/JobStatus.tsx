import React from 'react';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { Job, JobStatus as JobStatusType } from '../../types';

interface JobStatusProps {
  job: Job;
}

const statusConfig: Record<JobStatusType, { icon: React.ReactNode; color: string; text: string }> = {
  pending: {
    icon: <Clock className="h-5 w-5" />,
    color: 'text-yellow-600 bg-yellow-100',
    text: 'Pending',
  },
  processing: {
    icon: <Loader2 className="h-5 w-5 animate-spin" />,
    color: 'text-blue-600 bg-blue-100',
    text: 'Processing',
  },
  completed: {
    icon: <CheckCircle2 className="h-5 w-5" />,
    color: 'text-green-600 bg-green-100',
    text: 'Completed',
  },
  failed: {
    icon: <XCircle className="h-5 w-5" />,
    color: 'text-red-600 bg-red-100',
    text: 'Failed',
  },
};

export default function JobStatusBadge({ job }: JobStatusProps) {
  const config = statusConfig[job.status];

  return (
    <div className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full ${config.color}`}>
      {config.icon}
      <span className="text-sm font-medium">{config.text}</span>
    </div>
  );
}

export function JobProgress({ job }: JobStatusProps) {
  if (job.status !== 'processing') return null;

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm text-gray-600 mb-1">
        <span>Processing...</span>
        <span>{job.progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${job.progress}%` }}
        />
      </div>
    </div>
  );
}
