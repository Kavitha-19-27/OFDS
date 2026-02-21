import { useEffect, useState } from 'react';
import { useDocumentStore } from '../stores/documentStore';
import { FileUpload, DocumentList, DocumentStats } from '../components/documents';
import { Modal, Button } from '../components/common';
import toast from 'react-hot-toast';
import { getErrorMessage } from '../api';
import { 
  DocumentTextIcon, 
  CloudArrowUpIcon, 
  FolderOpenIcon,
  SparklesIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const DocumentsPage: React.FC = () => {
  const {
    documents,
    stats,
    isLoading,
    currentPage,
    totalPages,
    loadDocuments,
    loadStats,
    uploadDocument,
    deleteDocument,
    reprocessDocument,
  } = useDocumentStore();

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadDocuments();
    loadStats();
  }, [loadDocuments, loadStats]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      await uploadDocument(file);
      toast.success('Document uploaded successfully!');
      setShowUploadModal(false);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      toast.success('Document deleted');
      setDeleteId(null);
    } catch (err) {
      toast.error('Failed to delete document');
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await reprocessDocument(id);
      toast.success('Document queued for reprocessing');
    } catch (err) {
      toast.error('Failed to reprocess document');
    }
  };

  const filteredDocs = documents.filter(doc => 
    doc.original_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.filename?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-full bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-6 sm:mb-8 animate-fade-in">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="p-1.5 sm:p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg sm:rounded-xl shadow-lg shadow-blue-500/20">
              <FolderOpenIcon className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent">
                Documents
              </h1>
              <p className="text-xs sm:text-base text-gray-500 dark:text-gray-400 mt-0.5 sm:mt-1">Manage your knowledge base</p>
            </div>
          </div>
          <Button 
            onClick={() => setShowUploadModal(true)}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-700 hover:to-primary-600 shadow-lg shadow-primary-500/20 hover:shadow-xl transition-all text-sm sm:text-base"
          >
            <CloudArrowUpIcon className="h-4 w-4 sm:h-5 sm:w-5" />
            <span className="hidden sm:inline">Upload Document</span>
            <span className="sm:hidden">Upload</span>
          </Button>
        </div>

        {/* Stats */}
        <div className="mb-6 sm:mb-8 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <DocumentStats stats={stats} isLoading={!stats} />
        </div>

        {/* Search & Filter Bar */}
        <div className="mb-4 sm:mb-6 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 sm:pl-12 pr-4 py-2.5 sm:py-3 text-sm sm:text-base bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl border border-gray-200 dark:border-gray-700 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 dark:focus:ring-primary-900 outline-none transition-all text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
            />
          </div>
        </div>

        {/* Document List */}
        <div className="bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden animate-fade-in-up" style={{ animationDelay: '300ms' }}>
          {documents.length === 0 && !isLoading ? (
            <div className="p-8 sm:p-12 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700 dark:to-gray-600 rounded-xl sm:rounded-2xl mb-4 sm:mb-6">
                <DocumentTextIcon className="h-8 w-8 sm:h-10 sm:w-10 text-gray-400 dark:text-gray-300" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">No documents yet</h3>
              <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 mb-4 sm:mb-6 max-w-sm mx-auto">
                Upload your first document to start building your AI-powered knowledge base
              </p>
              <Button 
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center gap-2 text-sm sm:text-base"
              >
                <CloudArrowUpIcon className="h-4 w-4 sm:h-5 sm:w-5" />
                Upload Your First Document
              </Button>
            </div>
          ) : (
            <div className="p-6">
              <DocumentList
                documents={filteredDocs}
                onDelete={(id) => setDeleteId(id)}
                onReprocess={handleReprocess}
                isLoading={isLoading}
              />

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-center gap-2 pt-6 border-t dark:border-gray-700">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => loadDocuments(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    ← Previous
                  </Button>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).slice(
                      Math.max(0, currentPage - 3),
                      Math.min(totalPages, currentPage + 2)
                    ).map((page) => (
                      <button
                        key={page}
                        onClick={() => loadDocuments(page)}
                        className={`w-10 h-10 rounded-lg text-sm font-medium transition-all ${
                          page === currentPage
                            ? 'bg-primary-600 text-white shadow-lg'
                            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => loadDocuments(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next →
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tips Card */}
        <div className="mt-4 sm:mt-6 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl sm:rounded-2xl p-4 sm:p-5 border border-amber-100 dark:border-amber-800 animate-fade-in-up" style={{ animationDelay: '400ms' }}>
          <div className="flex items-start gap-3 sm:gap-4">
            <div className="p-1.5 sm:p-2 bg-amber-100 dark:bg-amber-900/50 rounded-lg">
              <SparklesIcon className="h-4 w-4 sm:h-5 sm:w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h4 className="font-semibold text-sm sm:text-base text-amber-900 dark:text-amber-100 mb-1">Pro Tips</h4>
              <ul className="text-xs sm:text-sm text-amber-800 dark:text-amber-200 space-y-0.5 sm:space-y-1">
                <li>• Supported: PDF, DOCX, TXT (max 50MB)</li>
                <li>• Auto-indexed for semantic search</li>
                <li className="hidden sm:block">• Larger documents may take a few minutes to process</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Upload Document"
        size="lg"
      >
        <FileUpload onUpload={handleUpload} isUploading={isUploading} />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Delete Document"
        size="sm"
      >
        <div className="text-center py-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
            <DocumentTextIcon className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Delete this document?</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            This action cannot be undone. The document and all its indexed data will be permanently removed.
          </p>
          <div className="flex justify-center gap-3">
            <Button variant="ghost" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={() => deleteId && handleDelete(deleteId)}>
              Delete Document
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DocumentsPage;
