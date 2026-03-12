// API Response Types
export interface ApiResponse<T = any> {
  status: string;
  message?: string;
  data?: T;
  error?: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  contextUsed?: ContextChunk[];
  contentFiltered?: boolean;
  crisisDetected?: boolean;
  totalTokensUsed?: number;
}

export interface ContextChunk {
  text: string;
  document: string;
  similarity: number;
  metadata?: {
    chunk_index: number;
    token_count: number;
    char_count: number;
    document_id: string;
    document_name: string;
    original_filename: string;
    description?: string;
    content_type: string;
  };
}

export interface ChatRequest {
  question: string;
  max_context_chunks?: number;
  collection_name?: string;
}

export interface ChatResponse {
  status: 'success' | 'content_filtered' | 'no_context' | 'error';
  question: string;
  answer: string;
  context_used?: ContextChunk[];
  content_warning?: boolean;
  crisis_detected?: boolean;
  content_filtered?: boolean;
  total_tokens_used?: number;
}

// Search Types
export interface SearchRequest {
  query: string;
  max_results?: number;
  collection_name?: string;
  filter_document?: string;
}

export interface SearchResult {
  text: string;
  metadata: {
    chunk_index: number;
    token_count: number;
    char_count: number;
    document_id: string;
    document_name: string;
    original_filename: string;
    description?: string;
    content_type: string;
  };
  similarity_score: number;
  distance: number;
}

export interface SearchResponse {
  status: string;
  search_query: string;
  results: {
    status: string;
    query: string;
    results_count: number;
    results: SearchResult[];
  };
}

// Upload Types
export interface UploadedDocument {
  id: string;
  name: string;
  chunks: number;
  status: 'success' | 'error' | 'uploading';
  description?: string;
  originalFilename?: string;
  uploadDate?: Date;
}

export interface UploadRequest {
  file: File;
  document_name?: string;
  description?: string;
  collection_name?: string;
}

export interface UploadResponse {
  status: string;
  message: string;
  data: {
    document_id: string;
    document_name: string;
    collection: string;
    chunks_stored: number;
    original_filename: string;
    description?: string;
  };
}

// Content Filter Types
export interface ContentFilterAnalysis {
  original_text: string;
  crisis_check: {
    crisis_detected: boolean;
    risk_level: 'none' | 'low' | 'medium' | 'high';
    triggered_keywords: string[];
    requires_intervention: boolean;
  };
  inappropriate_check: {
    has_profanity: boolean;
    has_explicit_content: boolean;
    censored_text: string;
    is_inappropriate: boolean;
  };
  should_block: boolean;
  allow_continue: boolean;
  filtered_response: string;
  crisis_response: string;
}

// Collection Types
export interface Collection {
  name: string;
  total_chunks: number;
  metadata: Record<string, any>;
  note?: string;
  error?: string;
}

export interface CollectionsResponse {
  status: string;
  collections: Collection[];
  note?: string;
}

// User Types (for future authentication)
export interface User {
  id: string;
  email: string;
  name?: string;
  isAuthenticated: boolean;
  role?: 'user' | 'counselor' | 'admin';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Component Props Types
export interface ChatInterfaceProps {
  onUploadClick: () => void;
  user?: User;
}

export interface DocumentUploadProps {
  isOpen: boolean;
  onClose: () => void;
  onDocumentUploaded: (doc: UploadedDocument) => void;
}

// Hook Types
export interface UseChatReturn {
  messages: ChatMessage[];
  sendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  clearChat: () => void;
}

export interface UseDocumentUploadReturn {
  uploadDocument: (request: UploadRequest) => Promise<UploadResponse>;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
}

// Error Types
export interface ApiError {
  detail: string | Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}

// Utility Types
export type MessageType = ChatMessage['type'];
export type UploadStatus = UploadedDocument['status'];
export type RiskLevel = ContentFilterAnalysis['crisis_check']['risk_level'];

// Constants
export const API_ENDPOINTS = {
  CHAT: '/api/v1/chat/chat',
  SEARCH: '/api/v1/chat/search',
  UPLOAD: '/api/v1/upload/pdf/to-vector-db',
  COLLECTIONS: '/api/v1/chat/collections',
  TEST_CONTENT_FILTER: '/api/v1/chat/test-content-filter',
  TEST_OPENAI: '/api/v1/rag/test-openai',
  TEST_EMBEDDING: '/api/v1/rag/test-embedding',
} as const;

export const CRISIS_KEYWORDS = [
  'suicide',
  'kill myself',
  'end my life',
  'want to die',
  'suicidal',
  'harm myself',
  'hurt myself',
] as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const ALLOWED_FILE_TYPES = ['application/pdf'] as const;
export const MAX_MESSAGE_LENGTH = 1000;
export const MAX_CONTEXT_CHUNKS = 5;