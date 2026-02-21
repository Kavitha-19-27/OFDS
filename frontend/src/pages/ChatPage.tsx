import { useEffect, useState } from 'react';
import { useChatStore } from '../stores/chatStore';
import { useSettingsStore } from '../stores/settingsStore';
import { ChatInput, ChatMessages, ChatSidebar } from '../components/chat';
import toast from 'react-hot-toast';
import { getErrorMessage } from '../api';
import { SparklesIcon, DocumentTextIcon, LightBulbIcon, ListBulletIcon, MagnifyingGlassIcon, ScaleIcon, ExclamationTriangleIcon, HeartIcon, Squares2X2Icon, QuestionMarkCircleIcon, Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import { LanguageSlider } from '../components/LanguageToggle';
import ThemeToggle from '../components/ThemeToggle';
import VoiceInput from '../components/VoiceInput';
import ExportChat from '../components/ExportChat';
import FavoritesPanel from '../components/FavoritesPanel';
import CustomTemplateModal from '../components/CustomTemplateModal';
import { useKeyboardShortcuts, ShortcutsModal } from '../components/KeyboardShortcuts';

// Templates for both languages
const templatesEnglish = [
  { icon: DocumentTextIcon, label: 'Summarize', prompt: 'Provide a structured summary of the documents including overview, key points, important conditions, and conclusions' },
  { icon: ListBulletIcon, label: 'Extract Facts', prompt: 'Extract the key facts, data points, and important information from my documents' },
  { icon: LightBulbIcon, label: 'Explain Term', prompt: 'What does the term "[TERM]" mean in the context of these documents? Explain its usage, implications, and significance.' },
  { icon: MagnifyingGlassIcon, label: 'Analyze', prompt: 'Analyze the document structure, identify its objective, key themes, rules, and responsibilities mentioned' },
  { icon: ScaleIcon, label: 'Compare', prompt: 'Compare and contrast the information across my uploaded documents, identifying similarities and differences' },
  { icon: ExclamationTriangleIcon, label: 'Risks', prompt: 'Identify any risks, warnings, penalties, or important implications stated in the documents' },
];

const templatesTanglish = [
  { icon: DocumentTextIcon, label: 'Summarize Pannu', prompt: 'Documents la irukura content ah summarize pannu - overview, key points, important conditions, conclusions ellam kudu da' },
  { icon: ListBulletIcon, label: 'Facts Extract', prompt: 'Documents la irundhu key facts, data points, important information ellam extract pannu da' },
  { icon: LightBulbIcon, label: 'Term Explain', prompt: '"[TERM]" nu enna da meaning? Documents context la explain pannu - usage, implications, significance ellam sollu' },
  { icon: MagnifyingGlassIcon, label: 'Analyze Pannu', prompt: 'Document structure analyze pannu - objective, key themes, rules, responsibilities ellam identify pannu da' },
  { icon: ScaleIcon, label: 'Compare Pannu', prompt: 'Documents ellathayum compare pannu da - similarities and differences identify pannu' },
  { icon: ExclamationTriangleIcon, label: 'Risks Sollu', prompt: 'Documents la irukura risks, warnings, penalties, important implications ellam identify pannu da' },
];

const ChatPage: React.FC = () => {
  const {
    messages,
    sessions,
    currentSessionId,
    isLoading,
    languageMode,
    sendMessage,
    loadSessions,
    loadSessionHistory,
    startNewSession,
    deleteSession,
    setLanguageMode,
  } = useChatStore();

  const { theme, setTheme } = useSettingsStore();

  const [showTemplates, setShowTemplates] = useState(true);
  const [showFavorites, setShowFavorites] = useState(false);
  const [showCustomTemplates, setShowCustomTemplates] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const [inputValue, setInputValue] = useState('');
  
  // Get templates based on language mode
  const quickTemplates = languageMode === 'tanglish' ? templatesTanglish : templatesEnglish;

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    setShowTemplates(messages.length === 0);
  }, [messages]);

  const handleSendMessage = async (question: string) => {
    try {
      setShowTemplates(false);
      await sendMessage(question);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    try {
      await loadSessionHistory(sessionId);
    } catch (err) {
      toast.error('Failed to load chat history');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      toast.success('Chat session deleted');
    } catch (err) {
      toast.error('Failed to delete session');
    }
  };

  const handleNewSession = () => {
    startNewSession();
    loadSessions();
    setShowTemplates(true);
  };

  const handleTemplateClick = (prompt: string) => {
    handleSendMessage(prompt);
  };

  const handleSelectTemplate = (content: string) => {
    setInputValue(content);
  };

  const handleVoiceTranscript = (transcript: string) => {
    setInputValue(transcript);
  };

  const handleSelectFavorite = (question: string) => {
    setShowFavorites(false);
    handleSendMessage(question);
  };
  
  // Keyboard shortcuts
  const { showHelp, setShowHelp } = useKeyboardShortcuts({
    onNewChat: handleNewSession,
    onToggleTheme: () => {
      const nextTheme = theme === 'light' ? 'dark' : 'light';
      setTheme(nextTheme);
      toast.success(`${nextTheme === 'dark' ? '🌙' : '☀️'} ${nextTheme.charAt(0).toUpperCase() + nextTheme.slice(1)} mode`);
    },
    onToggleLanguage: () => {
      const nextLang = languageMode === 'english' ? 'tanglish' : 'english';
      setLanguageMode(nextLang);
      toast.success(`Language: ${nextLang === 'tanglish' ? '🌶️ Tanglish' : '🇬🇧 English'}`);
    },
  });

  return (
    <div className="flex h-full bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Modals */}
      <ShortcutsModal isOpen={showHelp} onClose={() => setShowHelp(false)} />
      <FavoritesPanel 
        isOpen={showFavorites} 
        onClose={() => setShowFavorites(false)} 
        onSelectFavorite={handleSelectFavorite}
      />
      <CustomTemplateModal 
        isOpen={showCustomTemplates} 
        onClose={() => setShowCustomTemplates(false)} 
        onSelectTemplate={handleSelectTemplate}
      />

      {/* Sidebar */}
      <div className="hidden md:block">
        <ChatSidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
        />
      </div>

      {/* Mobile Sidebar */}
      {showMobileSidebar && (
        <>
          <div 
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={() => setShowMobileSidebar(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 w-72 md:hidden">
            <ChatSidebar
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSelectSession={(id) => {
                handleSelectSession(id);
                setShowMobileSidebar(false);
              }}
              onNewSession={() => {
                handleNewSession();
                setShowMobileSidebar(false);
              }}
              onDeleteSession={handleDeleteSession}
            />
          </div>
        </>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Top toolbar */}
        <div className="flex items-center justify-between px-2 sm:px-4 py-2 bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setShowMobileSidebar(true)}
              className="md:hidden p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Bars3Icon className="h-5 w-5" />
            </button>
            <LanguageSlider value={languageMode} onChange={setLanguageMode} />
          </div>
          <div className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => setShowFavorites(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg
                        text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="View favorites"
            >
              <HeartIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Favorites</span>
            </button>
            <button
              onClick={() => setShowCustomTemplates(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg
                        text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Template library"
            >
              <Squares2X2Icon className="h-4 w-4" />
              <span className="hidden sm:inline">Templates</span>
            </button>
            <ExportChat 
              messages={messages.flatMap(m => [
                { role: 'user' as const, content: m.question },
                { role: 'assistant' as const, content: m.answer }
              ])} 
            />
            <button
              onClick={() => setShowHelp(true)}
              className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Keyboard shortcuts (Ctrl+/)"
            >
              <QuestionMarkCircleIcon className="h-5 w-5" />
            </button>
            <ThemeToggle />
          </div>
        </div>

        {/* Chat content */}
        <div className="flex-1 flex flex-col relative">
          {showTemplates && messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-8 animate-fade-in overflow-y-auto">
              <div className="max-w-2xl w-full text-center">
                {/* Hero section */}
                <div className="mb-4 sm:mb-8">
                  <div className="inline-flex items-center justify-center w-14 h-14 sm:w-20 sm:h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl sm:rounded-2xl shadow-lg shadow-primary-500/30 mb-4 sm:mb-6">
                    <SparklesIcon className="h-7 w-7 sm:h-10 sm:w-10 text-white" />
                  </div>
                  <h2 className="text-xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2 sm:mb-3">
                    Document Intelligence 🚀
                  </h2>
                  <p className="text-sm sm:text-lg text-gray-500 dark:text-gray-400 mb-2 sm:mb-4 px-4">
                    {languageMode === 'tanglish' 
                      ? 'Enterprise-grade document analysis da! Zero-hallucination AI 💡' 
                      : 'Enterprise-grade document analysis with zero-hallucination AI 💡'}
                  </p>
                </div>

                {/* Template cards */}
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-4 mb-4 sm:mb-8 px-1">
                  {quickTemplates.map((template, index) => (
                    <button
                      key={template.label}
                      onClick={() => handleTemplateClick(template.prompt)}
                      className="group flex flex-col sm:flex-row items-start gap-2 sm:gap-4 p-3 sm:p-5 bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl border border-gray-100 dark:border-gray-700
                        hover:border-primary-200 dark:hover:border-primary-600 hover:shadow-lg hover:shadow-primary-500/10 
                        hover:-translate-y-1 transition-all duration-300 text-left animate-fade-in-up"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex-shrink-0 p-2 sm:p-3 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg sm:rounded-xl group-hover:from-primary-50 group-hover:to-primary-100 dark:group-hover:from-primary-900 dark:group-hover:to-primary-800 transition-colors">
                        <template.icon className="h-4 w-4 sm:h-6 sm:w-6 text-gray-600 dark:text-gray-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm sm:text-base text-gray-900 dark:text-white mb-0.5 sm:mb-1">{template.label}</h3>
                        <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 line-clamp-2 hidden sm:block">{template.prompt}</p>
                      </div>
                    </button>
                  ))}
                </div>

                {/* Tips */}
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 rounded-xl sm:rounded-2xl p-3 sm:p-4 border border-amber-100 dark:border-amber-800 mx-1">
                  <p className="text-xs sm:text-sm text-amber-800 dark:text-amber-200">
                    {languageMode === 'tanglish' 
                      ? <><span className="font-semibold">💡 Pro Tip:</span> Specific terms pathi kelu, summaries request pannu, risks analyze pannu. AI <span className="font-medium">document-grounded responses</span> kudum with source citations.</>
                      : <><span className="font-semibold">💡 Pro Tip:</span> Ask about specific terms, request structured summaries, or analyze risks and implications. The AI provides <span className="font-medium">strictly document-grounded responses</span> with source citations.</>
                    }
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <ChatMessages messages={messages} />
          )}
        </div>

        {/* Input area */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 px-4 py-2">
            <VoiceInput 
              onTranscript={handleVoiceTranscript} 
              disabled={isLoading}
            />
            <div className="flex-1">
              <ChatInput 
                onSend={handleSendMessage} 
                isLoading={isLoading} 
                initialValue={inputValue}
                onValueChange={setInputValue}
                placeholder={languageMode === 'tanglish' 
                  ? 'Documents pathi kelu da... or general questions um pudikkum! 🚀' 
                  : 'Ask about your documents or any general question... 🚀'
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
