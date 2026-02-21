import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatMessage, ChatSession } from '../types';
import { chatApi } from '../api/chat';

export type LanguageMode = 'english' | 'tanglish';

interface ChatState {
  messages: ChatMessage[];
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  languageMode: LanguageMode;
  
  // Actions
  sendMessage: (question: string) => Promise<void>;
  loadSessions: () => Promise<void>;
  loadSessionHistory: (sessionId: string) => Promise<void>;
  startNewSession: () => void;
  deleteSession: (sessionId: string) => Promise<void>;
  clearMessages: () => void;
  setLanguageMode: (mode: LanguageMode) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      sessions: [],
      currentSessionId: null,
      isLoading: false,
      languageMode: 'english',

      setLanguageMode: (mode: LanguageMode) => {
        set({ languageMode: mode });
      },

      sendMessage: async (question) => {
        const { currentSessionId, messages, languageMode } = get();
    
    // Add user message with loading state
    const userMessage: ChatMessage = {
      question,
      answer: '',
      isLoading: true,
    };
    
    set({ messages: [...messages, userMessage], isLoading: true });
    
    try {
      const response = await chatApi.send({
        question,
        session_id: currentSessionId || undefined,
        language_mode: languageMode,
      });
      
      // Update message with response
      const completedMessage: ChatMessage = {
        question: response.question,
        answer: response.answer,
        sources: response.sources,
        session_id: response.session_id,
        isLoading: false,
      };
      
      set((state) => ({
        messages: [...state.messages.slice(0, -1), completedMessage],
        currentSessionId: response.session_id,
        isLoading: false,
      }));
    } catch (error) {
      // Update message with error
      const errorMessage: ChatMessage = {
        question,
        answer: 'Sorry, I encountered an error processing your question. Please try again.',
        isLoading: false,
      };
      
      set((state) => ({
        messages: [...state.messages.slice(0, -1), errorMessage],
        isLoading: false,
      }));
      throw error;
    }
  },

  loadSessions: async () => {
    try {
      const response = await chatApi.getSessions();
      set({ sessions: response.sessions });
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  },

  loadSessionHistory: async (sessionId) => {
    set({ isLoading: true, currentSessionId: sessionId });
    
    try {
      const response = await chatApi.getHistory(sessionId, 1, 100);
      const messages: ChatMessage[] = response.history.map((item) => ({
        id: item.id,
        question: item.question,
        answer: item.answer,
        session_id: item.session_id,
        created_at: item.created_at,
        isLoading: false,
      }));
      
      set({ messages, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  startNewSession: () => {
    set({ messages: [], currentSessionId: null });
  },

  deleteSession: async (sessionId) => {
    try {
      await chatApi.deleteSession(sessionId);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.session_id !== sessionId),
        messages: state.currentSessionId === sessionId ? [] : state.messages,
        currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
      }));
    } catch (error) {
      throw error;
    }
  },

  clearMessages: () => {
    set({ messages: [], currentSessionId: null });
  },
}),
    {
      name: 'chat-language-storage',
      partialize: (state) => ({ languageMode: state.languageMode }),
    }
  )
);
