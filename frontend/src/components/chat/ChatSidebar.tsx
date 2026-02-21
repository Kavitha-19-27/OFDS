import { ChatSession } from '../../types';
import { ChatBubbleLeftIcon, TrashIcon, PlusIcon } from '@heroicons/react/24/outline';

interface ChatSidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}) => {
  return (
    <div className="w-64 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex flex-col">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
            No chat history yet
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`group flex items-center gap-2 rounded-lg p-2 cursor-pointer transition-colors ${
                  currentSessionId === session.session_id
                    ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-400'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
                onClick={() => onSelectSession(session.session_id)}
              >
                <ChatBubbleLeftIcon className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{session.first_message}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.session_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-400 hover:text-red-500 transition-all"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatSidebar;
