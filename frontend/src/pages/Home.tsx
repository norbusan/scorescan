import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, Music, FileText, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="bg-gradient-to-b from-primary-50 to-white">
      {/* Hero section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">
            Convert Music Scores
            <span className="block text-primary-600">in Seconds</span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto">
            Upload a photo of your music score and get a clean, transposable PDF. 
            Perfect for musicians, teachers, and students.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary text-lg px-8 py-3">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn btn-primary text-lg px-8 py-3">
                  Get Started Free
                </Link>
                <Link to="/login" className="btn btn-secondary text-lg px-8 py-3">
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Features section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="card p-6 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-100 text-primary-600 mb-4">
              <Upload className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              1. Upload Your Score
            </h3>
            <p className="text-gray-600">
              Take a photo with your phone or upload an existing image. 
              We support PNG, JPG, TIFF, and PDF files.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="card p-6 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-100 text-primary-600 mb-4">
              <Music className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              2. Choose Transposition
            </h3>
            <p className="text-gray-600">
              Optionally transpose your score by semitones or from one key to another. 
              Perfect for different instruments.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="card p-6 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-100 text-primary-600 mb-4">
              <FileText className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              3. Download PDF
            </h3>
            <p className="text-gray-600">
              Get a professionally engraved PDF of your score, 
              ready to print or share with others.
            </p>
          </div>
        </div>
      </div>

      {/* Technology section */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Powered by Advanced Technology
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              We use state-of-the-art optical music recognition to accurately 
              convert your handwritten or printed scores.
            </p>
          </div>
          <div className="flex flex-wrap justify-center items-center gap-8">
            <div className="flex items-center space-x-2 text-gray-600">
              <Zap className="h-5 w-5 text-primary-600" />
              <span>Audiveris OMR</span>
            </div>
            <div className="flex items-center space-x-2 text-gray-600">
              <Zap className="h-5 w-5 text-primary-600" />
              <span>MuseScore Engraving</span>
            </div>
            <div className="flex items-center space-x-2 text-gray-600">
              <Zap className="h-5 w-5 text-primary-600" />
              <span>music21 Transposition</span>
            </div>
          </div>
        </div>
      </div>

      {/* CTA section */}
      {!isAuthenticated && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="card bg-primary-600 p-8 sm:p-12 text-center">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
              Ready to Convert Your First Score?
            </h2>
            <p className="text-primary-100 mb-8 max-w-xl mx-auto">
              Create a free account and start converting music scores today. 
              No credit card required.
            </p>
            <Link to="/register" className="btn bg-white text-primary-600 hover:bg-primary-50 text-lg px-8 py-3">
              Get Started Free
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
