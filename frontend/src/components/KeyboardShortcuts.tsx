import { useEffect, useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ShortcutAction {
  key: string;
  description: string;
  category: string;
}

const SHORTCUTS: ShortcutAction[] = [
  { key: 'Ctrl + Enter', description: 'Send message', category: 'Chat' },
  { key: 'Ctrl + N', description: 'New chat / Clear', category: 'Chat' },
  { key: 'Ctrl + /', description: 'Show shortcuts', category: 'General' },
  { key: 'Ctrl + D', description: 'Toggle dark mode', category: 'General' },
  { key: 'Ctrl + L', description: 'Toggle language', category: 'General' },
  { key: 'Escape', description: 'Close modals', category: 'General' },
];

interface KeyboardShortcutsProps {
  onNewChat?: () => void;
  onToggleTheme?: () => void;
  onToggleLanguage?: () => void;
}

export const useKeyboardShortcuts = ({
  onNewChat,
  onToggleTheme,
  onToggleLanguage,
}: KeyboardShortcutsProps) => {
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if user is typing in an input
      const isTyping = ['INPUT', 'TEXTAREA'].includes(
        (e.target as HTMLElement)?.tagName || ''
      );

      // Ctrl + / - Show shortcuts help
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        setShowHelp((prev) => !prev);
        return;
      }

      // Escape - Close modals
      if (e.key === 'Escape') {
        setShowHelp(false);
        return;
      }

      // Don't trigger shortcuts while typing (except Ctrl+Enter)
      if (isTyping && !(e.ctrlKey && e.key === 'Enter')) {
        return;
      }

      // Ctrl + N - New chat
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        onNewChat?.();
        return;
      }

      // Ctrl + D - Toggle dark mode
      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        onToggleTheme?.();
        return;
      }

      // Ctrl + L - Toggle language
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        onToggleLanguage?.();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onNewChat, onToggleTheme, onToggleLanguage]);

  return { showHelp, setShowHelp };
};

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const categories = [...new Set(SHORTCUTS.map((s) => s.category))];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            ⌨️ Keyboard Shortcuts
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <XMarkIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Shortcuts List */}
        <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
          {categories.map((category) => (
            <div key={category}>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                {category}
              </h3>
              <div className="space-y-2">
                {SHORTCUTS.filter((s) => s.category === category).map((shortcut) => (
                  <div
                    key={shortcut.key}
                    className="flex items-center justify-between py-2"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-gray-700 
                                   text-gray-600 dark:text-gray-300 rounded border 
                                   border-gray-200 dark:border-gray-600">
                      {shortcut.key}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-center text-gray-500 dark:text-gray-400">
            Press <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs">Ctrl + /</kbd> anytime to toggle
          </p>
        </div>
      </div>
    </div>
  );
};

export default ShortcutsModal;
