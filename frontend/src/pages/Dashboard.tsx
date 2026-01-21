import React, { useState } from 'react';
import { Camera, Upload, Loader2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import DropZone from '../components/Upload/DropZone';
import CameraCapture from '../components/Upload/CameraCapture';
import TransposeOptions, { TransposeSettings } from '../components/Transpose/TransposeOptions';
import JobList from '../components/Jobs/JobList';
import { useJobs } from '../hooks/useJobs';
import { jobsApi } from '../api/client';

export default function Dashboard() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [transposeSettings, setTransposeSettings] = useState<TransposeSettings>({
    enabled: false,
    mode: 'semitones',
    semitones: 0,
    fromKey: 'C',
    toKey: 'C',
  });

  const {
    jobs,
    page,
    totalPages,
    isLoading,
    fetchJobs,
    deleteJob,
    setPage,
  } = useJobs(true, 3000); // Auto-refresh every 3 seconds

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleCameraCapture = (file: File) => {
    setSelectedFile(file);
    setShowCamera(false);
  };

  const handleClearFile = () => {
    setSelectedFile(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    setIsUploading(true);

    try {
      const options: { semitones?: number; fromKey?: string; toKey?: string } = {};

      if (transposeSettings.enabled) {
        if (transposeSettings.mode === 'semitones' && transposeSettings.semitones !== 0) {
          options.semitones = transposeSettings.semitones;
        } else if (transposeSettings.mode === 'keys') {
          options.fromKey = transposeSettings.fromKey;
          options.toKey = transposeSettings.toKey;
        }
      }

      await jobsApi.create(selectedFile, options);
      toast.success('Score uploaded! Processing will begin shortly.');
      setSelectedFile(null);
      setTransposeSettings({
        enabled: false,
        mode: 'semitones',
        semitones: 0,
        fromKey: 'C',
        toKey: 'C',
      });
      fetchJobs();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const message = err.response?.data?.detail || 'Failed to upload score';
      toast.error(message);
    } finally {
      setIsUploading(false);
    }
  };

  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-8">
        Dashboard
      </h1>

      {/* Upload section */}
      <div className="card p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Upload New Score
        </h2>

        {/* File input */}
        <DropZone
          onFileSelect={handleFileSelect}
          selectedFile={selectedFile}
          onClear={handleClearFile}
        />

        {/* Camera button (mobile) */}
        {isMobile && !selectedFile && (
          <button
            onClick={() => setShowCamera(true)}
            className="mt-4 w-full btn btn-secondary"
          >
            <Camera className="h-5 w-5 mr-2" />
            Take Photo
          </button>
        )}

        {/* Transpose options */}
        {selectedFile && (
          <div className="mt-6">
            <TransposeOptions onOptionsChange={setTransposeSettings} />
          </div>
        )}

        {/* Submit button */}
        {selectedFile && (
          <button
            onClick={handleSubmit}
            disabled={isUploading}
            className="mt-6 w-full btn btn-primary"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-5 w-5 mr-2" />
                Process Score
              </>
            )}
          </button>
        )}
      </div>

      {/* Jobs section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Your Conversions
          </h2>
          <button
            onClick={() => fetchJobs()}
            disabled={isLoading}
            className="btn btn-secondary text-sm"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {isLoading && jobs.length === 0 ? (
          <div className="card p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" />
            <p className="mt-4 text-gray-600">Loading jobs...</p>
          </div>
        ) : (
          <JobList
            jobs={jobs}
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            onDelete={deleteJob}
            onRefresh={fetchJobs}
          />
        )}
      </div>

      {/* Camera modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}
    </div>
  );
}
