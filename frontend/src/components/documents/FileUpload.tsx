import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon, CheckIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { Button } from '../common';

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
  maxSizeMB?: number;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUpload,
  isUploading = false,
  maxSizeMB = 10,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setError(null);
    
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setError(`File is too large. Maximum size is ${maxSizeMB}MB.`);
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError('Only PDF, DOCX, and TXT files are supported.');
      } else {
        setError('Invalid file. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, [maxSizeMB]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: maxSizeMB * 1024 * 1024,
    multiple: false,
    disabled: isUploading,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
    } catch (err) {
      // Error handled by parent
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setError(null);
  };

  const getFileIcon = () => {
    if (!selectedFile) return 'bg-gradient-to-br from-gray-400 to-gray-500';
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return 'bg-gradient-to-br from-red-500 to-rose-600';
      case 'docx': case 'doc': return 'bg-gradient-to-br from-blue-500 to-indigo-600';
      case 'txt': return 'bg-gradient-to-br from-gray-500 to-slate-600';
      default: return 'bg-gradient-to-br from-purple-500 to-violet-600';
    }
  };

  return (
    <div className="space-y-5">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300
          ${isDragActive 
            ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-blue-50 scale-[1.02]' 
            : 'border-gray-200 hover:border-primary-400 hover:bg-gradient-to-br hover:from-gray-50 hover:to-blue-50'
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className={`mx-auto w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all duration-300 ${
          isDragActive 
            ? 'bg-gradient-to-br from-primary-500 to-blue-600 shadow-lg shadow-primary-500/30' 
            : 'bg-gradient-to-br from-gray-100 to-gray-200'
        }`}>
          <CloudArrowUpIcon className={`h-8 w-8 transition-colors ${isDragActive ? 'text-white' : 'text-gray-500'}`} />
        </div>
        
        <p className="text-base text-gray-700 mb-2">
          {isDragActive ? (
            <span className="font-semibold text-primary-600">Drop your file here</span>
          ) : (
            <>
              <span className="font-semibold text-primary-600 hover:text-primary-700">Click to upload</span>
              <span className="text-gray-500"> or drag and drop</span>
            </>
          )}
        </p>
        <p className="text-sm text-gray-400">
          PDF, DOCX, or TXT up to {maxSizeMB}MB
        </p>

        {/* Decorative elements */}
        <div className="absolute top-4 right-4">
          <SparklesIcon className="h-5 w-5 text-gray-300" />
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-100 p-4 text-sm text-red-600 flex items-center gap-3">
          <div className="p-1 bg-red-100 rounded-lg">
            <XMarkIcon className="h-4 w-4 text-red-500" />
          </div>
          {error}
        </div>
      )}

      {selectedFile && !error && (
        <div className="rounded-xl border border-gray-200 bg-gradient-to-r from-gray-50 to-white p-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`flex items-center justify-center w-12 h-12 rounded-xl shadow-lg ${getFileIcon()}`}>
                <DocumentIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500 flex items-center gap-2">
                  <span>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                  <span className="inline-flex items-center gap-1 text-green-600">
                    <CheckIcon className="h-3 w-3" />
                    Ready to upload
                  </span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                size="sm"
                onClick={handleUpload}
                isLoading={isUploading}
                className="shadow-lg shadow-primary-500/20"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </Button>
              <button
                onClick={clearSelection}
                disabled={isUploading}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
