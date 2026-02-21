import ReactMarkdown from 'react-markdown';
import { ChatMessage, SourceChunk } from '../../types';
import { DocumentTextIcon, ChevronDownIcon, ChevronUpIcon, SparklesIcon, UserCircleIcon, ClipboardDocumentIcon, HandThumbUpIcon, HandThumbDownIcon } from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpSolid, HandThumbDownIcon as HandThumbDownSolid } from '@heroicons/react/24/solid';
import { useState } from 'react';
import FavoriteButton from '../FavoriteButton';
import toast from 'react-hot-toast';
import { chatApi } from '../../api/chat';

interface ChatMessageItemProps {
  message: ChatMessage;
}

const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const [feedback, setFeedback] = useState<number | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  const handleFeedback = async (rating: number) => {
    if (isSubmittingFeedback) return;
    
    // Toggle off if clicking same rating
    if (feedback === rating) {
      setFeedback(null);
      return;
    }

    setIsSubmittingFeedback(true);
    try {
      // Use message id or generate one from index
      const messageId = parseInt(message.id?.toString() || '0') || Date.now();
      await chatApi.submitFeedback({
        message_id: messageId,
        session_id: parseInt(message.session_id?.toString() || '0') || 0,
        rating,
      });
      setFeedback(rating);
      toast.success(rating === 1 ? '👍 Thanks for the feedback!' : '👎 Thanks, we\'ll improve!');
    } catch (error) {
      console.error('Feedback submission failed:', error);
      // Still set locally for UX
      setFeedback(rating);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* User question */}
      <div className="flex justify-end gap-3">
        <div className="max-w-[80%] group">
          <div className="bg-gradient-to-r from-primary-600 to-primary-500 rounded-2xl rounded-tr-md px-5 py-3.5 text-white shadow-lg shadow-primary-500/20">
            <p className="text-[15px] leading-relaxed">{message.question}</p>
          </div>
        </div>
        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-md">
          <UserCircleIcon className="h-5 w-5 text-white" />
        </div>
      </div>

      {/* AI response */}
      <div className="flex justify-start gap-3">
        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-md">
          <SparklesIcon className="h-5 w-5 text-white" />
        </div>
        <div className="max-w-[80%] space-y-3">
          <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-md px-5 py-4 shadow-sm border border-gray-100 dark:border-gray-700">
            {message.isLoading ? (
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2.5 h-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2.5 h-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm text-gray-400 dark:text-gray-500 ml-2">Thinking...</span>
              </div>
            ) : (
              <>
                <div className="prose prose-sm max-w-none prose-p:text-gray-700 prose-p:leading-relaxed prose-headings:text-gray-900 prose-strong:text-gray-800 prose-code:text-primary-600 prose-code:bg-primary-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded dark:prose-p:text-gray-300 dark:prose-headings:text-white dark:prose-strong:text-gray-200">
                  <ReactMarkdown>{message.answer}</ReactMarkdown>
                </div>
                {/* Actions */}
                <div className="flex items-center gap-1 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                  <FavoriteButton 
                    question={message.question} 
                    answer={message.answer} 
                    size="sm" 
                  />
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(message.answer);
                      toast.success('Copied! 📋');
                    }}
                    className="p-1 rounded-lg text-gray-400 hover:text-blue-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    title="Copy response"
                  >
                    <ClipboardDocumentIcon className="h-4 w-4" />
                  </button>
                  <div className="w-px h-4 bg-gray-200 dark:bg-gray-600 mx-1" />
                  <button
                    onClick={() => handleFeedback(1)}
                    disabled={isSubmittingFeedback}
                    className={`p-1 rounded-lg transition-colors ${
                      feedback === 1
                        ? 'text-green-500 bg-green-50 dark:bg-green-900/30'
                        : 'text-gray-400 hover:text-green-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    title="Good response"
                  >
                    {feedback === 1 ? (
                      <HandThumbUpSolid className="h-4 w-4" />
                    ) : (
                      <HandThumbUpIcon className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    onClick={() => handleFeedback(-1)}
                    disabled={isSubmittingFeedback}
                    className={`p-1 rounded-lg transition-colors ${
                      feedback === -1
                        ? 'text-red-500 bg-red-50 dark:bg-red-900/30'
                        : 'text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    title="Needs improvement"
                  >
                    {feedback === -1 ? (
                      <HandThumbDownSolid className="h-4 w-4" />
                    ) : (
                      <HandThumbDownIcon className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && !message.isLoading && (
            <div>
              <button
                onClick={() => setShowSources(!showSources)}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-xs font-medium text-gray-600 dark:text-gray-300 transition-colors"
              >
                <DocumentTextIcon className="h-4 w-4" />
                {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                {showSources ? (
                  <ChevronUpIcon className="h-3 w-3" />
                ) : (
                  <ChevronDownIcon className="h-3 w-3" />
                )}
              </button>

              {showSources && (
                <div className="mt-3 space-y-2 animate-fade-in-down">
                  {message.sources.map((source, index) => (
                    <SourceItem key={source.chunk_id || index} source={source} index={index} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const SourceItem: React.FC<{ source: SourceChunk; index: number }> = ({ source, index }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div 
      className="rounded-xl border border-gray-100 dark:border-gray-700 bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-750 p-4 text-sm hover:shadow-md transition-shadow animate-fade-in-up"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
            <DocumentTextIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <span className="font-medium text-gray-800 dark:text-white">{source.document_name}</span>
            {source.page_number && (
              <span className="ml-2 text-gray-400 dark:text-gray-500 text-xs">Page {source.page_number}</span>
            )}
          </div>
        </div>
        <span className="flex-shrink-0 px-2 py-1 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400 text-xs font-medium rounded-full">
          {(source.relevance_score * 100).toFixed(0)}% match
        </span>
      </div>
      <div className="mt-3 pl-9">
        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
          {expanded ? source.content_preview : source.content_preview.slice(0, 180)}
          {source.content_preview.length > 180 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="ml-1 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
            >
              {expanded ? 'Show less' : '...Read more'}
            </button>
          )}
        </p>
      </div>
    </div>
  );
};

export default ChatMessageItem;
