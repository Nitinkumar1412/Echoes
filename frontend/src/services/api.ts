// Centralized API Service for Echoes Platform
// Maps every backend route to a typed frontend function.
import axios from 'axios';
import type {
  AuthResponse,
  ChunkItem,
  DocumentItem,
  GraphData,
  GraphEdgeData,
  GraphNodeData,
  QueryResult,
  TimelineItem,
  UserProfileResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const DEFAULT_WORKSPACE_ID = 'ws_default';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Attach Bearer token from localStorage to all outgoing requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('echoes_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function resolveWorkspaceId(workspaceId?: string): string {
  if (workspaceId && workspaceId !== DEFAULT_WORKSPACE_ID) {
    return workspaceId;
  }
  const stored = localStorage.getItem('echoes_workspace_id');
  return stored || workspaceId || DEFAULT_WORKSPACE_ID;
}

// ─── Additional Types for backend-specific shapes ─────────────────────────────

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  document_name: string;
  text: string;
  score: number;
  rank: number;
  page_number: number;
  retrieval_method: string;
}

export interface SearchResponse {
  workspace_id: string;
  query: string;
  total_results: number;
  results: SearchResultItem[];
  timing_ms: Record<string, number>;
}

export interface EntityItem {
  entity_id: string;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  mention_count: number;
  document_count: number;
}

export interface EntityListResponse {
  workspace_id: string;
  total_entities: number;
  entities: EntityItem[];
}

// ─── Helper: map backend GraphEdge (from_node/to_node) to frontend (from/to) ──
// Backend GraphEdge schema uses from_node/to_node field names in JSON output.
// Frontend GraphEdgeData type uses from/to. This mapper bridges the gap.
function mapEdge(e: any): GraphEdgeData {
  return {
    id: e.id || `${e.from || e.from_node}_${e.to || e.to_node}`,
    from: e.from || e.from_node || '',
    to: e.to || e.to_node || '',
    label: e.label || 'CONNECTED_TO',
    confidence: e.confidence ?? 1.0,
    evidence_count: e.evidence_count ?? 1,
  };
}

// ─── API Client ───────────────────────────────────────────────────────────────

export const echoesApi = {

  // ── 1. Health ─────────────────────────────────────────────────────────────
  // GET /health
  async checkHealth(): Promise<{ status: string; database: string }> {
    try {
      const res = await client.get('/health');
      return res.data;
    } catch {
      return { status: 'offline', database: 'disconnected' };
    }
  },

  // ── 2. Auth: Register ─────────────────────────────────────────────────────
  // POST /api/v1/auth/register  Body: { email, password, display_name }
  async register(email: string, password: string, displayName: string): Promise<AuthResponse> {
    const res = await client.post('/api/v1/auth/register', {
      email,
      password,
      display_name: displayName,
    });
    return res.data;
  },

  // ── 3. Auth: Login ────────────────────────────────────────────────────────
  // POST /api/v1/auth/login  Body: { email, password }
  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await client.post('/api/v1/auth/login', { email, password });
    return res.data;
  },

  // ── 4. Auth: Google OAuth ─────────────────────────────────────────────────
  // POST /api/v1/auth/google  Body: { credential?, email?, display_name?, avatar_url? }
  async loginWithGoogle(params: {
    credential?: string;
    email?: string;
    displayName?: string;
    avatarUrl?: string;
  }): Promise<AuthResponse> {
    const res = await client.post('/api/v1/auth/google', {
      credential: params.credential,
      email: params.email,
      display_name: params.displayName,
      avatar_url: params.avatarUrl,
    });
    return res.data;
  },

  // ── 5. Auth: Get current user ─────────────────────────────────────────────
  // GET /api/v1/auth/me
  async getMe(): Promise<UserProfileResponse> {
    const res = await client.get('/api/v1/auth/me');
    return res.data;
  },

  // ── 6. Auth: Logout ───────────────────────────────────────────────────────
  // POST /api/v1/auth/logout
  async logout(): Promise<void> {
    try {
      await client.post('/api/v1/auth/logout');
    } catch {
      // Ignored — JWT is stateless; clearing local storage is sufficient
    }
  },

  // ── 7. Documents: Upload ──────────────────────────────────────────────────
  // POST /api/v1/workspaces/{ws}/documents/upload  multipart/form-data
  async uploadDocument(
    file: File,
    workspaceId?: string,
    onProgress?: (pct: number) => void
  ): Promise<{ document: DocumentItem; is_duplicate: boolean; chunks_created: number }> {
    const ws = resolveWorkspaceId(workspaceId);
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post(
      `/api/v1/workspaces/${ws}/documents/upload`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (onProgress && e.total) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        },
      }
    );
    return res.data;
  },

  // ── 8. Documents: List ────────────────────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/documents?skip=0&limit=50
  async getDocuments(workspaceId?: string, skip = 0, limit = 50): Promise<DocumentItem[]> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(`/api/v1/workspaces/${ws}/documents`, {
        params: { skip, limit },
      });
      return res.data.documents || [];
    } catch {
      return [];
    }
  },

  // ── 9. Documents: Get single ──────────────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/documents/{document_id}
  async getDocument(documentId: string, workspaceId?: string): Promise<DocumentItem | null> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(`/api/v1/workspaces/${ws}/documents/${documentId}`);
      return res.data;
    } catch {
      return null;
    }
  },

  // ── 10. Documents: Get chunks ─────────────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/documents/{document_id}/chunks
  // Returns ChunkResponse[] directly (not wrapped in an object)
  async getDocumentChunks(documentId: string, workspaceId?: string): Promise<ChunkItem[]> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(
        `/api/v1/workspaces/${ws}/documents/${documentId}/chunks`
      );
      return Array.isArray(res.data) ? res.data : [];
    } catch {
      return [];
    }
  },

  // ── 10b. Documents: Download / View URL ───────────────────────────────────
  getDocumentDownloadUrl(documentId: string, workspaceId?: string): string {
    const ws = resolveWorkspaceId(workspaceId);
    return `${API_BASE}/api/v1/workspaces/${ws}/documents/${documentId}/download`;
  },

  // ── 10c. Documents: Delete ───────────────────────────────────────────────
  async deleteDocument(documentId: string, workspaceId?: string): Promise<boolean> {
    const ws = resolveWorkspaceId(workspaceId);
    await client.delete(`/api/v1/workspaces/${ws}/documents/${documentId}`);
    return true;
  },

  // ── 11. Search: Hybrid retrieval ─────────────────────────────────────────
  // POST /api/v1/workspaces/{ws}/search  Body: { query, top_k, document_ids? }
  // Returns ranked chunks with scores (lower-level than askQuestion)
  async hybridSearch(
    query: string,
    workspaceId?: string,
    topK = 10,
    documentIds?: string[]
  ): Promise<SearchResponse> {
    const ws = resolveWorkspaceId(workspaceId);
    const res = await client.post(`/api/v1/workspaces/${ws}/search`, {
      query,
      top_k: topK,
      document_ids: documentIds ?? null,
    });
    return res.data;
  },

  // ── 12. Query: Ask question (full RAG pipeline) ───────────────────────────
  // POST /api/v1/workspaces/{ws}/query  Body: { query, document_ids?, top_k }
  async askQuestion(
    query: string,
    workspaceId?: string,
    documentIds?: string[]
  ): Promise<QueryResult> {
    const ws = resolveWorkspaceId(workspaceId);
    const res = await client.post(`/api/v1/workspaces/${ws}/query`, {
      query,
      document_ids: documentIds ?? null,
      top_k: 10,
    });
    return res.data;
  },

  // ── 13. Query: History ────────────────────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/query/history?limit=20
  async getQueryHistory(workspaceId?: string, limit = 20): Promise<QueryResult[]> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(`/api/v1/workspaces/${ws}/query/history`, {
        params: { limit },
      });
      return res.data.queries || [];
    } catch {
      return [];
    }
  },

  // ── 14. Graph: Full workspace knowledge graph ─────────────────────────────
  // GET /api/v1/workspaces/{ws}/graph
  // IMPORTANT FIX: Backend serializes edges as from_node/to_node (Pydantic field names).
  // Frontend GraphEdgeData uses from/to. mapEdge() translates between them.
  async getGraph(workspaceId?: string): Promise<GraphData> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(`/api/v1/workspaces/${ws}/graph`);
      const data = res.data;
      return {
        workspace_id: data.workspace_id,
        nodes: (data.nodes || []) as GraphNodeData[],
        edges: (data.edges || []).map(mapEdge),
      };
    } catch {
      return { workspace_id: ws, nodes: [], edges: [] };
    }
  },

  // ── 15. Graph: Timeline of events ────────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/timeline?limit=50
  async getTimeline(workspaceId?: string, limit = 50): Promise<TimelineItem[]> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(`/api/v1/workspaces/${ws}/timeline`, {
        params: { limit },
      });
      return res.data.events || [];
    } catch {
      return [];
    }
  },

  // ── 16. Graph: List entities ──────────────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/entities?entity_type=PERSON&limit=100
  async listEntities(
    workspaceId?: string,
    entityType?: string,
    limit = 100
  ): Promise<EntityListResponse> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(`/api/v1/workspaces/${ws}/entities`, {
        params: {
          ...(entityType ? { entity_type: entityType } : {}),
          limit,
        },
      });
      return res.data;
    } catch {
      return { workspace_id: ws, total_entities: 0, entities: [] };
    }
  },

  // ── 17. Graph: Entity ego subgraph ───────────────────────────────────────
  // GET /api/v1/workspaces/{ws}/entities/{entity_id}/ego?radius=1
  async getEntityEgoGraph(
    entityId: string,
    workspaceId?: string,
    radius = 1
  ): Promise<GraphData> {
    const ws = resolveWorkspaceId(workspaceId);
    try {
      const res = await client.get(
        `/api/v1/workspaces/${ws}/entities/${entityId}/ego`,
        { params: { radius } }
      );
      const data = res.data;
      return {
        workspace_id: data.workspace_id,
        nodes: (data.nodes || []) as GraphNodeData[],
        edges: (data.edges || []).map(mapEdge),
      };
    } catch {
      return { workspace_id: ws, nodes: [], edges: [] };
    }
  },
};

export const api = echoesApi;
