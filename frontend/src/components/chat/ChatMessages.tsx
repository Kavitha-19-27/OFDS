import { useEffect, useRef } from 'react';
import { ChatMessage } from '../../types';
import ChatMessageItem from './ChatMessage';
import { ChatBubbleLeftRightIcon, SparklesIcon } from '@heroicons/react/24/outline';

interface ChatMessagesProps {
  messages: ChatMessage[];
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-gray-500 dark:text-gray-400 p-8">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-400 to-purple-500 rounded-full blur-2xl opacity-20 animate-pulse" />
          <div className="relative bg-gradient-to-br from-primary-500 to-purple-600 p-4 rounded-2xl shadow-lg">
            <SparklesIcon className="h-12 w-12 text-white" />
          </div>
        </div>
        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mt-6 mb-2">Start a conversation</h3>
        <p className="text-gray-500 dark:text-gray-400 text-center max-w-sm">
          Ask questions about your uploaded documents and get AI-powered answers instantly
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {messages.map((message, index) => (
          <div 
            key={message.id || index} 
            className="animate-fade-in-up"
            style={{ animationDelay: `${Math.min(index * 50, 300)}ms` }}
          >
            <ChatMessageItem message={message} />
          </div>
        ))}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
};

export default ChatMessages;
