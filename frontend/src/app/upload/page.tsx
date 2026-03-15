'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'image/jpeg',
  'image/png',
  'text/plain',
];

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.jpg', '.jpeg', '.png', '.txt'];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function UploadPage() {
  const router = useRouter();
  const { logout } = useAuthStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState('en');
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    setError('');

    // Validate file type
    const fileExtension = '.' + selectedFile.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
      setError(
        `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`
      );
      return;
    }

    if (!ALLOWED_TYPES.includes(selectedFile.type) && selectedFile.type !== '') {
      setError(
        `Invalid file type. Allowed: PDF, DOCX, JPG, PNG, TXT`
      );
      return;
    }

    // Validate file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
      return;
    }

    setFile(selectedFile);
  };

  const handleUploadAndAnalyze = async () => {
    if (!file) return;

    setError('');
    setUploading(true);
    setUploadProgress(0);

    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });

      const documentId = uploadResponse.data.document_id;

      // Analyze document
      setUploading(false);
      setAnalyzing(true);

      await api.post('/analyze', {
        document_id: documentId,
        language: language,
      });

      // Redirect to results
      router.push(`/results/${documentId}`);
    } catch (err: any) {
      if (err.response?.status === 401) {
        logout();
        router.push('/login');
      } else if (err.response?.status === 429) {
        setError('Rate limit exceeded. Please try again in a few minutes.');
      } else {
        setError(
          err.response?.data?.detail || 'Upload failed. Please try again.'
        );
      }
      setUploading(false);
      setAnalyzing(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
                LegalLens
              </Link>
              <div className="hidden md:flex space-x-4">
                <Link
                  href="/dashboard"
                  className="text-gray-700 hover:text-blue-600 font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  href="/upload"
                  className="text-blue-600 font-medium border-b-2 border-blue-600"
                >
                  Upload
                </Link>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-700 hover:text-red-600 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-4xl">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Legal Document</h1>
          <p className="text-gray-600 mb-8">
            Upload your rental agreement, employment contract, or any legal document for AI-powered
            analysis
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* File Upload Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : file
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-blue-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {!file ? (
              <>
                <div className="text-6xl mb-4">📄</div>
                <p className="text-xl font-semibold text-gray-700 mb-2">
                  Drag and drop your file here
                </p>
                <p className="text-gray-500 mb-4">or</p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium"
                >
                  Browse Files
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept={ALLOWED_EXTENSIONS.join(',')}
                  onChange={handleFileInput}
                />
                <p className="text-sm text-gray-500 mt-4">
                  Supported: PDF, DOCX, JPG, PNG, TXT (Max 10MB)
                </p>
              </>
            ) : (
              <>
                <div className="text-6xl mb-4">✅</div>
                <p className="text-xl font-semibold text-gray-900 mb-2">{file.name}</p>
                <p className="text-gray-600 mb-4">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
                <button
                  onClick={() => setFile(null)}
                  className="text-red-600 hover:text-red-700 font-medium"
                >
                  Remove File
                </button>
              </>
            )}
          </div>

          {/* Language Selection */}
          {file && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="te">తెలుగు (Telugu)</option>
                <option value="ta">தமிழ் (Tamil)</option>
                <option value="kn">ಕನ್ನಡ (Kannada)</option>
                <option value="mr">मराठी (Marathi)</option>
              </select>
            </div>
          )}

          {/* Upload Progress */}
          {(uploading || analyzing) && (
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-700 mb-2">
                <span>
                  {uploading && 'Uploading...'}
                  {analyzing && 'Analyzing document...'}
                </span>
                {uploading && <span>{uploadProgress}%</span>}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    analyzing ? 'bg-blue-600 animate-pulse w-full' : 'bg-blue-600'
                  }`}
                  style={{ width: analyzing ? '100%' : `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-4 mt-8">
            <button
              onClick={handleUploadAndAnalyze}
              disabled={!file || uploading || analyzing}
              className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {uploading
                ? 'Uploading...'
                : analyzing
                ? 'Analyzing...'
                : 'Upload & Analyze'}
            </button>
            <Link
              href="/dashboard"
              className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium text-center"
            >
              Cancel
            </Link>
          </div>

          {/* Info Box */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">What happens next?</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Your document will be securely uploaded and encrypted</li>
              <li>• AI will analyze the contract for risks and key clauses</li>
              <li>• You'll get plain-language explanations in your chosen language</li>
              <li>• Results include risk score, alerts, and negotiation tips</li>
              <li>• Your file will be auto-deleted after 7 days</li>
            </ul>
          </div>

          {/* Supported Documents */}
          <div className="mt-8">
            <h3 className="font-semibold text-gray-900 mb-3">Supported Documents:</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">🏠</div>
                <p className="text-sm text-gray-700">Rental Agreements</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">💼</div>
                <p className="text-sm text-gray-700">Employment Contracts</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">🤝</div>
                <p className="text-sm text-gray-700">Service Agreements</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">📋</div>
                <p className="text-sm text-gray-700">General Contracts</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
