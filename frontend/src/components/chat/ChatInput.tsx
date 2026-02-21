import { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, SparklesIcon   } from '@heroicons/react/24/solid';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  initialValue?: string;
  onValueChange?: (value: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isLoading = false,
  placeholder = 'Ask about your documents or any general question... 🚀',
  initialValue = '',
  onValueChange,
}) => {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync with external value
  useEffect(() => {
    if (initialValue && initialValue !== message) {
      setMessage(initialValue);
    }
  }, [initialValue]);

  const handleChange = (value: string) => {
    setMessage(value);
    onValueChange?.(value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim());
      setMessage('');
      onValueChange?.('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  return (
    <div className="p-4 max-w-4xl mx-auto w-full">
      <form 
        onSubmit={handleSubmit} 
        className={`relative flex items-end gap-3 p-2 bg-white dark:bg-gray-800 rounded-2xl border-2 transition-all duration-200 shadow-lg ${
          isFocused 
            ? 'border-primary-400 shadow-primary-500/10' 
            : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
        }`}
      >
        {/* Decorative gradient */}
        <div className={`absolute inset-0 bg-gradient-to-r from-primary-500/5 to-purple-500/5 rounded-2xl transition-opacity ${isFocused ? 'opacity-100' : 'opacity-0'}`} />
        
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className="w-full resize-none bg-transparent px-4 py-3 text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none disabled:bg-transparent disabled:text-gray-500"
          />
        </div>
        
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className={`relative flex h-12 w-12 items-center justify-center rounded-xl font-medium transition-all duration-200 ${
            message.trim() && !isLoading
              ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 hover:-translate-y-0.5'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          ) : (
            <PaperAirplaneIcon className="h-5 w-5" />
          )}
        </button>
      </form>
      
      {/* Helper text */}
      <p className="text-center text-xs text-gray-400 mt-3">
        <SparklesIcon className="inline h-3 w-3 mr-1" />
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
};

export default ChatInput;
