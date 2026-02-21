import { useState } from 'react';
import {
  XMarkIcon,
  HeartIcon,
  TrashIcon,
  ClipboardDocumentIcon,
} from '@heroicons/react/24/outline';
import { useSettingsStore } from '../stores/settingsStore';
import toast from 'react-hot-toast';

interface FavoritesPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectFavorite?: (question: string) => void;
}

const FavoritesPanel: React.FC<FavoritesPanelProps> = ({
  isOpen,
  onClose,
  onSelectFavorite,
}) => {
  const { favorites, removeFavorite } = useSettingsStore();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard! 📋');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <HeartIcon className="h-5 w-5 text-red-500" />
            ⭐ Saved Favorites
            <span className="text-sm font-normal text-gray-500">
              ({favorites.length})
            </span>
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <XMarkIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Favorites List */}
        <div className="flex-1 overflow-y-auto p-4">
          {favorites.length === 0 ? (
            <div className="text-center py-12">
              <HeartIcon className="h-12 w-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                No favorites yet
              </p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Click the heart icon on any response to save it here
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {favorites.map((fav) => (
                <div
                  key={fav.id}
                  className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 
                            hover:border-blue-300 dark:hover:border-blue-600 transition-colors"
                >
                  {/* Question */}
                  <div className="flex items-start justify-between gap-2">
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => onSelectFavorite?.(fav.question)}
                    >
                      <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                        Q: {fav.question}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleCopy(fav.answer)}
                        className="p-1.5 text-gray-400 hover:text-blue-500 rounded transition-colors"
                        title="Copy answer"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => removeFavorite(fav.id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 rounded transition-colors"
                        title="Remove from favorites"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Answer (collapsible) */}
                  <div className="mt-2">
                    <p
                      className={`text-sm text-gray-600 dark:text-gray-300 ${
                        expandedId === fav.id ? '' : 'line-clamp-3'
                      }`}
                    >
                      {fav.answer}
                    </p>
                    {fav.answer.length > 200 && (
                      <button
                        onClick={() =>
                          setExpandedId(expandedId === fav.id ? null : fav.id)
                        }
                        className="text-xs text-blue-500 hover:text-blue-600 mt-1"
                      >
                        {expandedId === fav.id ? 'Show less' : 'Show more'}
                      </button>
                    )}
                  </div>

                  {/* Meta */}
                  <div className="mt-2 text-xs text-gray-400">
                    Saved {formatDate(fav.createdAt)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {favorites.length > 0 && (
          <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-center text-gray-500 dark:text-gray-400">
              Click a question to ask it again • Favorites are saved locally
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FavoritesPanel;
