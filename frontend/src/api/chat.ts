import api from './client';
import { ChatRequest, ChatResponse, ChatSession } from '../types';

interface ChatHistoryResponse {
  history: Array<{
    id: string;
    question: string;
    answer: string;
    session_id: string;
    created_at: string;
  }>;
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface ChatSessionsResponse {
  sessions: ChatSession[];
  total: number;
}

// Feedback types
export interface FeedbackRequest {
  message_id: number;
  session_id: number;
  rating: number; // 1 for 👍, -1 for 👎
  feedback_text?: string;
  issue_type?: string;
}

export interface FeedbackResponse {
  id: number;
  message: string;
}

export interface FeedbackListItem {
  id: string;
  message_id: number;
  session_id: number;
  user_id: string;
  user_email: string;
  user_name?: string;
  rating: number;
  feedback_text?: string;
  issue_type?: string;
  created_at: string;
}

export interface FeedbackListResponse {
  feedback: FeedbackListItem[];
  total: number;
  page: number;
  total_pages: number;
}

export interface FeedbackStats {
  period_days: number;
  total_feedback: number;
  positive: number;
  negative: number;
  satisfaction_rate: number;
  issue_breakdown: Record<string, number>;
  daily_trend: Record<string, { positive: number; negative: number }>;
}

export const chatApi = {
  send: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', data);
    return response.data;
  },

  getHistory: async (
    sessionId?: string,
    page = 1,
    pageSize = 20
  ): Promise<ChatHistoryResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (sessionId) {
      params.append('session_id', sessionId);
    }
    const response = await api.get<ChatHistoryResponse>(`/chat/history?${params}`);
    return response.data;
  },

  getSessions: async (): Promise<ChatSessionsResponse> => {
    const response = await api.get<ChatSessionsResponse>('/chat/sessions');
    return response.data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/chat/sessions/${sessionId}`);
  },

  // Feedback methods
  submitFeedback: async (data: FeedbackRequest): Promise<FeedbackResponse> => {
    const response = await api.post<FeedbackResponse>('/v2/feedback', data);
    return response.data;
  },

  getFeedbackStats: async (days = 30): Promise<FeedbackStats> => {
    const response = await api.get<FeedbackStats>(`/v2/feedback/stats?days=${days}`);
    return response.data;
  },

  getFeedbackList: async (
    page = 1,
    pageSize = 20,
    rating?: number
  ): Promise<FeedbackListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (rating !== undefined) {
      params.append('rating', rating.toString());
    }
    const response = await api.get<FeedbackListResponse>(`/v2/feedback/list?${params}`);
    return response.data;
  },
};
