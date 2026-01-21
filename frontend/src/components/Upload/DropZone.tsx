import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image, FileText, X } from 'lucide-react';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
}

const ACCEPTED_TYPES = {
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/tiff': ['.tiff', '.tif'],
  'application/pdf': ['.pdf'],
};

export default function DropZone({ onFileSelect, selectedFile, onClear }: DropZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    multiple: false,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  if (selectedFile) {
    return (
      <div className="border-2 border-primary-300 bg-primary-50 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary-100 rounded-lg">
              {selectedFile.type.startsWith('image/') ? (
                <Image className="h-6 w-6 text-primary-600" />
              ) : (
                <FileText className="h-6 w-6 text-primary-600" />
              )}
            </div>
            <div>
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>
          <button
            onClick={onClear}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
            aria-label="Remove file"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-primary-400 bg-primary-50'
          : isDragReject
          ? 'border-red-400 bg-red-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
      }`}
    >
      <input {...getInputProps()} />
      <Upload
        className={`mx-auto h-12 w-12 ${
          isDragActive ? 'text-primary-500' : 'text-gray-400'
        }`}
      />
      <p className="mt-4 text-lg font-medium text-gray-700">
        {isDragActive ? 'Drop your score here' : 'Drag & drop your music score'}
      </p>
      <p className="mt-2 text-sm text-gray-500">
        or click to browse files
      </p>
      <p className="mt-4 text-xs text-gray-400">
        Supports PNG, JPG, TIFF, PDF (max 50MB)
      </p>
    </div>
  );
}
