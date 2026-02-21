import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  PaperAirplaneIcon,
  SparklesIcon,
  UserCircleIcon,
  DocumentTextIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common';
import PromptLimitModal from './PromptLimitModal';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface GuestChatProps {
  documentName: string;
  sessionId: string;
  onBack: () => void;
}

const MAX_TRIAL_PROMPTS = 10;

const GuestChat: React.FC<GuestChatProps> = ({ documentName, sessionId, onBack }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get prompt count from localStorage
  const getPromptCount = () => {
    return parseInt(localStorage.getItem('trial_prompt_count') || '0', 10);
  };

  const [promptCount, setPromptCount] = useState(getPromptCount());

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Welcome message - only run on mount
  useEffect(() => {
    const initialCount = getPromptCount();
    const remaining = MAX_TRIAL_PROMPTS - initialCount;
    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'assistant',
      content: `🎉 Welcome! I'm ready to help you analyze "${documentName}". 

You have **${remaining} free prompts** remaining. Ask me anything about your document!

Try questions like:
- "Summarize this document"
- "What are the key points?"
- "Explain the main concepts"`,
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    // Check prompt limit
    if (promptCount >= MAX_TRIAL_PROMPTS) {
      setShowLimitModal(true);
      return;
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    const messageToSend = input.trim();
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/trial/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: messageToSend,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', response.status, errorText);
        throw new Error(`Chat request failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('Chat response:', data);

      // Update prompt count
      const newCount = promptCount + 1;
      setPromptCount(newCount);
      localStorage.setItem('trial_prompt_count', newCount.toString());

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response || data.answer || 'I processed your request.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Check if limit reached after this prompt
      if (newCount >= MAX_TRIAL_PROMPTS) {
        setTimeout(() => setShowLimitModal(true), 1000);
      }
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `❌ Error: ${error.message || 'Something went wrong'}. Check console for details.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const remainingPrompts = MAX_TRIAL_PROMPTS - promptCount;

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] sm:h-[600px] bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white">
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={onBack}
            className="p-1.5 sm:p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <ArrowLeftIcon className="h-4 w-4 sm:h-5 sm:w-5" />
          </button>
          <div className="p-1.5 sm:p-2 bg-white/20 rounded-lg">
            <DocumentTextIcon className="h-4 w-4 sm:h-5 sm:w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-sm sm:text-base truncate max-w-[120px] sm:max-w-[200px]">{documentName}</h3>
            <p className="text-[10px] sm:text-xs text-white/80">Trial Chat</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 bg-white/20 rounded-full">
          <SparklesIcon className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          <span className="text-xs sm:text-sm font-medium">{remainingPrompts} left</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-300"
          style={{ width: `${(promptCount / MAX_TRIAL_PROMPTS) * 100}%` }}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-2 sm:gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center ${
                message.role === 'user'
                  ? 'bg-gradient-to-br from-primary-500 to-purple-600'
                  : 'bg-gradient-to-br from-emerald-500 to-teal-600'
              }`}
            >
              {message.role === 'user' ? (
                <UserCircleIcon className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
              ) : (
                <SparklesIcon className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
              )}
            </div>
            <div
              className={`max-w-[85%] sm:max-w-[80%] rounded-xl sm:rounded-2xl px-3 sm:px-4 py-2 sm:py-3 ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-primary-600 to-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="text-sm prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <SparklesIcon className="h-5 w-5 text-white animate-spin" />
            </div>
            <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 sm:p-4 border-t border-gray-200 dark:border-gray-700">
        {remainingPrompts <= 3 && remainingPrompts > 0 && (
          <div className="mb-2 sm:mb-3 px-2 sm:px-3 py-1.5 sm:py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <p className="text-xs sm:text-sm text-amber-700 dark:text-amber-300 text-center">
              ⚠️ Only <span className="font-bold">{remainingPrompts}</span> free prompts remaining!
            </p>
          </div>
        )}
        <div className="flex gap-2 sm:gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={remainingPrompts > 0 ? "Ask about your document..." : "Trial limit reached"}
            disabled={isLoading || remainingPrompts === 0}
            className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base bg-gray-100 dark:bg-gray-700 rounded-lg sm:rounded-xl border-0 focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 disabled:opacity-50"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || remainingPrompts === 0}
            className="px-3 sm:px-4 bg-gradient-to-r from-primary-600 to-purple-600"
          >
            <PaperAirplaneIcon className="h-4 w-4 sm:h-5 sm:w-5" />
          </Button>
        </div>
      </form>

      {/* Limit Modal */}
      <PromptLimitModal
        isOpen={showLimitModal}
        onClose={() => setShowLimitModal(false)}
        promptsUsed={promptCount}
        maxPrompts={MAX_TRIAL_PROMPTS}
      />
    </div>
  );
};

export default GuestChat;
