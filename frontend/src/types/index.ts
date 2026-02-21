// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  tenant_id: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export enum UserRole {
  ADMIN = 'ADMIN',
  USER = 'USER',
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  tenant_name: string;
  email: string;
  password: string;
  full_name: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
  tenant_id: string;
  user_id: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface SignupResponse {
  user_id: string;
  tenant_id: string;
  email: string;
  role: string;
  message: string;
}

// Tenant types
export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  max_documents: number;
  max_storage_mb: number;
  created_at: string;
  updated_at: string;
}

export interface TenantStats {
  tenant_id: string;
  document_count: number;
  total_chunks: number;
  storage_used_mb: number;
  user_count: number;
  query_count_today: number;
  query_count_total: number;
}

// Document types
export interface Document {
  id: string;
  tenant_id: string;
  original_name: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  chunk_count: number | null;
  page_count: number | null;
  error_message: string | null;
  uploaded_by: string;
  created_at: string;
  processed_at: string | null;
}

export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DocumentStats {
  total_documents: number;
  pending_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  total_chunks: number;
  total_storage_mb: number;
}

// Chat types
export interface ChatMessage {
  id?: string;
  question: string;
  answer: string;
  sources?: SourceChunk[];
  session_id?: string;
  created_at?: string;
  isLoading?: boolean;
}

export interface SourceChunk {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content_preview: string;
  page_number: number | null;
  relevance_score: number;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
  top_k?: number;
  language_mode?: 'english' | 'tanglish';
}

export interface ChatResponse {
  answer: string;
  question: string;
  session_id: string;
  sources: SourceChunk[];
  model_used: string;
  tokens_used: number;
  latency_ms: number;
}

export interface ChatSession {
  session_id: string;
  message_count: number;
  first_message: string;
  last_message: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}
