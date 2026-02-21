import { create } from 'zustand';
import { Document, DocumentStats } from '../types';
import { documentApi } from '../api/documents';

interface DocumentState {
  documents: Document[];
  stats: DocumentStats | null;
  isLoading: boolean;
  currentPage: number;
  totalPages: number;
  total: number;
  
  // Actions
  loadDocuments: (page?: number) => Promise<void>;
  loadStats: () => Promise<void>;
  uploadDocument: (file: File) => Promise<Document>;
  deleteDocument: (id: string) => Promise<void>;
  reprocessDocument: (id: string) => Promise<void>;
}

export const useDocumentStore = create<DocumentState>()((set, get) => ({
  documents: [],
  stats: null,
  isLoading: false,
  currentPage: 1,
  totalPages: 1,
  total: 0,

  loadDocuments: async (page = 1) => {
    set({ isLoading: true });
    try {
      const response = await documentApi.list(page, 20);
      set({
        documents: response.documents,
        currentPage: response.page,
        totalPages: response.pages,
        total: response.total,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  loadStats: async () => {
    try {
      const stats = await documentApi.getStats();
      set({ stats });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  },

  uploadDocument: async (file) => {
    set({ isLoading: true });
    try {
      const document = await documentApi.upload(file);
      set((state) => ({
        documents: [document, ...state.documents],
        isLoading: false,
      }));
      // Reload stats
      get().loadStats();
      return document;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  deleteDocument: async (id) => {
    try {
      await documentApi.delete(id);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== id),
      }));
      // Reload stats
      get().loadStats();
    } catch (error) {
      throw error;
    }
  },

  reprocessDocument: async (id) => {
    try {
      const document = await documentApi.reprocess(id);
      set((state) => ({
        documents: state.documents.map((d) => (d.id === id ? document : d)),
      }));
    } catch (error) {
      throw error;
    }
  },
}));
