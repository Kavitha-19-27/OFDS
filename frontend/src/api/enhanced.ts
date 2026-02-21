/**
 * Enhanced API client for v2 endpoints.
 * Includes feedback, templates, quotas, analytics.
 */
import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

// Create axios instance for v2 API
const apiV2 = axios.create({
  baseURL: '/api/v1/v2',  // Note: v2 is mounted under v1 router
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to add auth token
apiV2.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============== Types ==============

export interface FeedbackRequest {
  message_id: number;
  session_id: number;
  rating: number;
  feedback_text?: string;
  issue_type?: string;
}

export interface FeedbackResponse {
  id: number;
  message: string;
}

export interface QuotaStatus {
  documents: { used: number; limit: number; remaining: number; percentage: number };
  storage_mb: { used: number; limit: number; remaining: number; percentage: number };
  queries_today: { used: number; limit: number; remaining: number; percentage: number };
  tokens_today: { used: number; limit: number; remaining: number; percentage: number };
  resets_at: string;
}

export interface Template {
  id: string;
  name: string;
  prompt_template: string;
  description?: string;
  category: string;
  is_system: boolean;
}

export interface CreateTemplateRequest {
  name: string;
  prompt_template: string;
  category?: string;
  description?: string;
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

export interface ActivitySummary {
  tenant_id: number;
  period_days: number;
  active_users: number;
  total_actions: number;
  action_breakdown: Record<string, number>;
  daily_activity: Record<string, number>;
}

export interface CacheStats {
  total_cached: number;
  hit_rate: number;
  total_hits: number;
  avg_ttl_remaining: number;
}

export interface RateLimitStatus {
  rpm_used: number;
  rpm_limit: number;
  rpm_remaining: number;
  tpm_used: number;
  tpm_limit: number;
  tpm_remaining: number;
}

// ============== API Functions ==============

/**
 * Submit feedback on a chat response.
 */
export const submitFeedback = async (
  feedback: FeedbackRequest
): Promise<FeedbackResponse> => {
  const response = await apiV2.post<FeedbackResponse>('/feedback', feedback);
  return response.data;
};

/**
 * Get feedback statistics.
 */
export const getFeedbackStats = async (
  days: number = 30
): Promise<FeedbackStats> => {
  const response = await apiV2.get<FeedbackStats>('/feedback/stats', {
    params: { days }
  });
  return response.data;
};

/**
 * Get current quota status.
 */
export const getQuotaStatus = async (): Promise<QuotaStatus> => {
  const response = await apiV2.get<QuotaStatus>('/quota');
  return response.data;
};

/**
 * Get rate limit status.
 */
export const getRateLimitStatus = async (): Promise<RateLimitStatus> => {
  const response = await apiV2.get<RateLimitStatus>('/rate-limit');
  return response.data;
};

/**
 * Get available templates.
 */
export const getTemplates = async (
  category?: string
): Promise<Template[]> => {
  const response = await apiV2.get<Template[]>('/templates', {
    params: category ? { category } : undefined
  });
  return response.data;
};

/**
 * Create a custom template.
 */
export const createTemplate = async (
  template: CreateTemplateRequest
): Promise<Template> => {
  const response = await apiV2.post<Template>('/templates', template);
  return response.data;
};

/**
 * Delete a custom template.
 */
export const deleteTemplate = async (templateId: number): Promise<void> => {
  await apiV2.delete(`/templates/${templateId}`);
};

/**
 * Get activity analytics.
 */
export const getActivityAnalytics = async (
  days: number = 7
): Promise<ActivitySummary> => {
  const response = await apiV2.get<ActivitySummary>('/analytics/activity', {
    params: { days }
  });
  return response.data;
};

/**
 * Get cache statistics.
 */
export const getCacheStats = async (): Promise<CacheStats> => {
  const response = await apiV2.get<CacheStats>('/analytics/cache');
  return response.data;
};

/**
 * Get audit logs.
 */
export const getAuditLogs = async (params: {
  action?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}): Promise<Array<{
  id: number;
  action: string;
  resource_type?: string;
  resource_id?: number;
  user_id: number;
  details?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}>> => {
  const response = await apiV2.get('/audit-logs', { params });
  return response.data;
};

export default apiV2;
