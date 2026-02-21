import api from './client';
import { Document, DocumentStats } from '../types';

interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const documentApi = {
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<Document>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  list: async (page = 1, pageSize = 20, status?: string): Promise<DocumentListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) {
      params.append('status_filter', status);
    }
    const response = await api.get<DocumentListResponse>(`/documents?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Document> => {
    const response = await api.get<Document>(`/documents/${id}`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
  },

  reprocess: async (id: string): Promise<Document> => {
    const response = await api.post<Document>(`/documents/${id}/reprocess`);
    return response.data;
  },

  getStats: async (): Promise<DocumentStats> => {
    const response = await api.get<DocumentStats>('/documents/stats');
    return response.data;
  },
};
