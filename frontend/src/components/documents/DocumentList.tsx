import { Document } from '../../types';
import {
  DocumentIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  CubeIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common';

interface DocumentListProps {
  documents: Document[];
  onDelete: (id: string) => void;
  onReprocess: (id: string) => void;
  isLoading?: boolean;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onDelete,
  onReprocess,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse rounded-xl border border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 p-5">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-gray-200 dark:bg-gray-700" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-1/3 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-3 w-1/2 bg-gray-100 dark:bg-gray-600 rounded" />
              </div>
              <div className="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700 dark:to-gray-600 rounded-2xl mb-4">
          <DocumentTextIcon className="h-8 w-8 text-gray-400 dark:text-gray-300" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">No documents yet</h3>
        <p className="text-gray-500 dark:text-gray-400">
          Upload your first document to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {documents.map((doc, idx) => (
        <DocumentItem
          key={doc.id}
          document={doc}
          onDelete={onDelete}
          onReprocess={onReprocess}
          index={idx}
        />
      ))}
    </div>
  );
};

interface DocumentItemProps {
  document: Document;
  onDelete: (id: string) => void;
  onReprocess: (id: string) => void;
  index: number;
}

const DocumentItem: React.FC<DocumentItemProps> = ({
  document,
  onDelete,
  onReprocess,
  index,
}) => {
  const getStatusBadge = () => {
    switch (document.status?.toUpperCase()) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
            <CheckCircleIcon className="h-3.5 w-3.5" />
            Ready
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 border border-red-200">
            <ExclamationCircleIcon className="h-3.5 w-3.5" />
            Failed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
            <ArrowPathIcon className="h-3.5 w-3.5 animate-spin" />
            Processing
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
            <ClockIcon className="h-3.5 w-3.5" />
            Pending
          </span>
        );
    }
  };

  const getFileIcon = () => {
    const ext = document.original_name?.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return 'bg-gradient-to-br from-red-500 to-rose-600';
      case 'docx':
      case 'doc':
        return 'bg-gradient-to-br from-blue-500 to-indigo-600';
      case 'txt':
        return 'bg-gradient-to-br from-gray-500 to-slate-600';
      default:
        return 'bg-gradient-to-br from-purple-500 to-violet-600';
    }
  };

  return (
    <div 
      className="flex items-center gap-4 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:shadow-md hover:border-gray-200 dark:hover:border-gray-600 transition-all duration-300 group animate-fade-in-up"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex-shrink-0">
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl shadow-lg ${getFileIcon()}`}>
          <DocumentIcon className="h-6 w-6 text-white" />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
            {document.original_name}
          </p>
          {getStatusBadge()}
        </div>
        
        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          {document.status?.toUpperCase() === 'COMPLETED' && (
            <>
              <span className="inline-flex items-center gap-1">
                <CubeIcon className="h-3.5 w-3.5" />
                {document.chunk_count} chunks
              </span>
              <span className="inline-flex items-center gap-1">
                <DocumentTextIcon className="h-3.5 w-3.5" />
                {document.page_count} pages
              </span>
            </>
          )}
          {document.status?.toUpperCase() === 'FAILED' && (
            <span className="text-red-500">{document.error_message || 'Processing failed'}</span>
          )}
          <span>{document.file_size ? (document.file_size / 1024 / 1024).toFixed(2) : '0.00'} MB</span>
          <span>Uploaded {document.created_at ? new Date(document.created_at).toLocaleDateString() : 'Recently'}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        {document.status?.toUpperCase() === 'FAILED' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onReprocess(document.id)}
            title="Reprocess"
            className="text-blue-600 hover:bg-blue-50"
          >
            <ArrowPathIcon className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(document.id)}
          className="text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
          title="Delete"
        >
          <TrashIcon className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default DocumentList;
