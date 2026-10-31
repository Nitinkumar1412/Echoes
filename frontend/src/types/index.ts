// Frontend TypeScript Interfaces for Echoes Platform

export type EntityType = 'PERSON' | 'ORGANIZATION' | 'PROJECT' | 'CONCEPT' | 'LOCATION' | 'TECHNOLOGY' | 'DECISION' | 'OTHER';

export type EventType = 'MILESTONE' | 'DECISION' | 'MEETING' | 'DISCUSSION' | 'TASK' | 'OTHER';

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  excerpt: string;
  relevance_score: number;
}

export interface TimelineItem {
  event_id: string;
  title: string;
  normalized_date?: string | null;
  event_type?: string;
  original_expression?: string;
  date_precision?: string;
  participants?: string[];
}

export interface PerformanceMetrics {
  total_ms: number;
  retrieval_ms: number;
  reranking_ms: number;
  generation_ms: number;
}

export interface QueryResult {
  query_id: string;
  workspace_id: string;
  query: string;
  answer: string;
  confidence: 'high' | 'medium' | 'low' | 'insufficient_evidence';
  has_uncertainty: boolean;
  citations: Citation[];
  timeline: TimelineItem[];
  performance: PerformanceMetrics;
  created_at: string;
}

export interface GraphNodeData {
  id: string;
  label: string;
  type: EntityType;
  mentions: number;
}

export interface GraphEdgeData {
  id: string;
  from: string;
  to: string;
  label: string;
  confidence: number;
  evidence_count: number;
}

export interface GraphData {
  workspace_id: string;
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
}

export interface DocumentItem {
  document_id: string;
  workspace_id: string;
  file: {
    original_name: string;
    file_type: string;
    size_bytes: number;
    sha256_hash: string;
    storage_url?: string | null;
    storage_provider?: string;
  };
  content_meta: {
    page_count?: number;
    word_count?: number;
    extracted_title?: string;
  };
  processing: {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    chunk_count: number;
    indexed_chunk_count: number;
    error_message?: string | null;
  };
  created_at: string;
}

export interface ChunkItem {
  chunk_id: string;
  document_id: string;
  workspace_id: string;
  text: string;
  token_count: number;
  chunk_index: number;
  page_number?: number;
  section_heading?: string;
  char_start: number;
  char_end: number;
  is_indexed: boolean;
}

export interface MemoryStats {
  totalDocuments: number;
  totalChunks: number;
  totalEntities: number;
  totalEvents: number;
  totalQueries: number;
}

// ── Authentication Types ──────────────────────────────────────────────────────

export interface User {
  user_id: string;
  email: string;
  display_name: string;
  avatar_url?: string | null;
  is_active: boolean;
  settings?: {
    default_workspace_id?: string;
    result_limit?: number;
    preferred_language?: string;
  };
  created_at?: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  workspace_id: string;
  user: User;
}

export interface UserProfileResponse {
  user: User;
  workspace_id: string | null;
  workspaces: Array<{
    workspace_id: string;
    name: string;
    description?: string;
    role?: string;
  }>;
}
