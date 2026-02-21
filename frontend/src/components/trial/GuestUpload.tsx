import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  XMarkIcon,
  SparklesIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common';
import toast from 'react-hot-toast';

interface GuestUploadProps {
  onUploadComplete: (file: File, response: any) => void;
  isDisabled?: boolean;
}

const GuestUpload: React.FC<GuestUploadProps> = ({ onUploadComplete, isDisabled }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const hasUsedTrial = localStorage.getItem('trial_upload_used') === 'true';

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB for trial
    maxFiles: 1,
    disabled: isDisabled || hasUsedTrial,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/v1/trial/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      
      // Mark trial as used
      localStorage.setItem('trial_upload_used', 'true');
      localStorage.setItem('trial_document_id', data.document_id || '');
      localStorage.setItem('trial_session_id', data.session_id || '');

      toast.success('Document uploaded successfully! 🎉');
      onUploadComplete(selectedFile, data);
    } catch (error) {
      toast.error('Upload failed. Please try again.');
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
  };

  if (hasUsedTrial) {
    return (
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl sm:rounded-2xl p-5 sm:p-8 border-2 border-amber-200 dark:border-amber-800 text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 bg-amber-100 dark:bg-amber-900/50 rounded-full mb-3 sm:mb-4">
          <CheckCircleIcon className="h-6 w-6 sm:h-8 sm:w-8 text-amber-600 dark:text-amber-400" />
        </div>
        <h3 className="text-lg sm:text-xl font-bold text-amber-900 dark:text-amber-100 mb-2">
          Trial Upload Complete! 🎉
        </h3>
        <p className="text-sm sm:text-base text-amber-700 dark:text-amber-300 mb-4">
          Nee already oru document upload pannittey. Create account for unlimited access!
        </p>
        <div className="flex flex-col gap-2 sm:gap-3 justify-center">
          <Button
            onClick={() => window.location.href = '/register'}
            className="bg-gradient-to-r from-primary-600 to-purple-600 text-sm sm:text-base"
          >
            🚀 Create Free Account
          </Button>
          <Button
            variant="ghost"
            onClick={() => window.location.href = '/login'}
            className="text-sm sm:text-base"
          >
            Login
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl sm:rounded-2xl p-5 sm:p-8 text-center cursor-pointer
          transition-all duration-300
          ${isDragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[1.02]'
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800/50'
          }
          ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-3 sm:space-y-4">
          <div className={`
            inline-flex items-center justify-center w-14 h-14 sm:w-20 sm:h-20 rounded-xl sm:rounded-2xl
            transition-all duration-300
            ${isDragActive
              ? 'bg-gradient-to-br from-primary-500 to-purple-600 scale-110'
              : 'bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700 dark:to-gray-600'
            }
          `}>
            <CloudArrowUpIcon className={`h-7 w-7 sm:h-10 sm:w-10 ${isDragActive ? 'text-white' : 'text-gray-400 dark:text-gray-300'}`} />
          </div>

          <div>
            <p className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-1">
              {isDragActive ? '📁 Drop it here!' : '🆓 Upload Your First Document FREE'}
            </p>
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
              Drag & drop or tap to select (PDF, DOCX, TXT - Max 10MB)
            </p>
          </div>

          {/* Trial Badge */}
          <div className="inline-flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 rounded-full border border-green-200 dark:border-green-800">
            <SparklesIcon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-600 dark:text-green-400" />
            <span className="text-xs sm:text-sm font-medium text-green-700 dark:text-green-300">
              No signup required!
            </span>
          </div>
        </div>
      </div>

      {/* Selected File */}
      {selectedFile && (
        <div className="bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl border border-gray-200 dark:border-gray-700 p-3 sm:p-4 animate-fade-in">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="p-2 sm:p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg sm:rounded-xl shadow-lg">
              <DocumentTextIcon className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm sm:text-base text-gray-900 dark:text-white truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={removeFile}
              className="p-1.5 sm:p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-4 w-4 sm:h-5 sm:w-5" />
            </button>
          </div>

          {/* Progress Bar */}
          {isUploading && (
            <div className="mt-4">
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-500 to-purple-500 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 text-center">
                Uploading... {uploadProgress}%
              </p>
            </div>
          )}

          {/* Upload Button */}
          {!isUploading && (
            <Button
              onClick={handleUpload}
              className="w-full mt-4 bg-gradient-to-r from-primary-600 to-purple-600 shadow-lg"
            >
              <CloudArrowUpIcon className="h-5 w-5 mr-2" />
              Upload & Analyze Document
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default GuestUpload;
