import React, { useRef, useState, useCallback } from 'react';
import { Camera, X, RotateCcw, Check } from 'lucide-react';

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onClose: () => void;
}

export default function CameraCapture({ onCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsStreaming(true);
        setError(null);
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setError('Could not access camera. Please check permissions.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const capture = useCallback(() => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.9);
        setCapturedImage(imageData);
        stopCamera();
      }
    }
  }, [stopCamera]);

  const retake = useCallback(() => {
    setCapturedImage(null);
    startCamera();
  }, [startCamera]);

  const confirmCapture = useCallback(() => {
    if (capturedImage && canvasRef.current) {
      canvasRef.current.toBlob(
        (blob) => {
          if (blob) {
            const file = new File([blob], `score_${Date.now()}.jpg`, {
              type: 'image/jpeg',
            });
            onCapture(file);
          }
        },
        'image/jpeg',
        0.9
      );
    }
  }, [capturedImage, onCapture]);

  const handleClose = useCallback(() => {
    stopCamera();
    onClose();
  }, [stopCamera, onClose]);

  // Start camera on mount
  React.useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-black/50">
        <h2 className="text-white font-medium">Take a photo of your score</h2>
        <button
          onClick={handleClose}
          className="p-2 text-white hover:bg-white/20 rounded-full transition-colors"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Camera view */}
      <div className="flex-1 relative">
        {error ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-white p-4">
              <p className="text-lg mb-4">{error}</p>
              <button
                onClick={startCamera}
                className="btn btn-primary"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : capturedImage ? (
          <img
            src={capturedImage}
            alt="Captured score"
            className="w-full h-full object-contain"
          />
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="w-full h-full object-contain"
          />
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      {/* Controls */}
      <div className="p-4 bg-black/50 flex items-center justify-center space-x-6">
        {capturedImage ? (
          <>
            <button
              onClick={retake}
              className="flex flex-col items-center text-white p-3 hover:bg-white/20 rounded-lg transition-colors"
            >
              <RotateCcw className="h-8 w-8 mb-1" />
              <span className="text-sm">Retake</span>
            </button>
            <button
              onClick={confirmCapture}
              className="flex flex-col items-center text-white bg-primary-600 p-4 rounded-full hover:bg-primary-700 transition-colors"
            >
              <Check className="h-10 w-10" />
            </button>
          </>
        ) : (
          <button
            onClick={capture}
            disabled={!isStreaming}
            className="p-4 bg-white rounded-full disabled:opacity-50 hover:bg-gray-100 transition-colors"
          >
            <Camera className="h-10 w-10 text-gray-900" />
          </button>
        )}
      </div>
    </div>
  );
}
