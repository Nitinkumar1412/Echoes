import React, { useState, useEffect, useRef } from 'react';
import {
  FolderGit2,
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  FileUp,
  Layers,
  Clock,
  Eye,
  Trash2,
  RefreshCw,
  X,
  Cloud,
  Download,
  ExternalLink,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import type { DocumentItem, ChunkItem } from '../types';

export const SourcesPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [selectedDocChunks, setSelectedDocChunks] = useState<ChunkItem[] | null>(null);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [activeDocName, setActiveDocName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    try {
      const data = await echoesApi.getDocuments();
      setDocuments(data);
    } catch (e) {
      console.error('Failed to fetch documents:', e);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadMessage(null);

    const file = files[0];
    try {
      const res = await echoesApi.uploadDocument(file);
      const isDup = res.is_duplicate;
      setUploadMessage(
        isDup
          ? `File '${file.name}' already existed in workspace (SHA-256 deduplicated).`
          : `Successfully ingested '${file.name}' (${res.chunks_created} chunks generated and vectorized).`
      );
      await fetchDocs();
    } catch (err: any) {
      setUploadMessage(`Upload error: ${err.message || 'Failed to process document'}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const inspectChunks = async (doc: DocumentItem) => {
    setActiveDocName(doc.file.original_name);
    setLoadingChunks(true);
    setSelectedDocChunks(null);
    try {
      const chunks = await echoesApi.getDocumentChunks(doc.document_id);
      setSelectedDocChunks(chunks);
    } catch {
      setSelectedDocChunks([]);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleDeleteDocument = async (docId: string, docName: string) => {
    if (!window.confirm(`Delete "${docName}"? This will permanently remove all associated chunks, vector embeddings, and storage files.`)) {
      return;
    }
    try {
      await echoesApi.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message || 'Unknown error'}`);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-[#232336]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#A78BFA] font-bold mb-1">
            <FolderGit2 className="h-4 w-4" />
            Knowledge Repository
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF] tracking-tight">
            Source Documents & Ingestion
          </h1>
          <p className="text-sm text-[#9292A5] mt-1">
            Upload personal documents, PDFs, DOCX, and notes. Boundary-aware chunked & indexed into ChromaDB.
          </p>
        </div>

        <button
          onClick={fetchDocs}
          className="flex items-center gap-2 rounded-xl bg-[#151521] border border-[#232336] px-3.5 py-2 text-xs font-semibold text-[#9292A5] hover:text-[#F5F3FF]"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="rounded-3xl border-2 border-dashed border-[#232336] hover:border-[#8B5CF6]/60 bg-[#101019]/60 hover:bg-[#151521]/60 p-8 text-center transition-all cursor-pointer group shadow-xl"
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg"
          onChange={handleFileUpload}
        />
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="h-14 w-14 rounded-2xl bg-[#8B5CF6]/15 flex items-center justify-center text-[#A78BFA] border border-[#8B5CF6]/30 group-hover:scale-110 transition-transform">
            {uploading ? (
              <div className="h-6 w-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Upload className="h-7 w-7" />
            )}
          </div>
          <div>
            <span className="text-base font-bold text-[#F5F3FF] block">
              {uploading ? 'Processing & Vectorizing Document...' : 'Click to Upload or Drag and Drop'}
            </span>
            <span className="text-xs text-[#9292A5] mt-1 block">
              Supported: PDF, DOCX, TXT, Markdown, PNG, JPG (Max 50MB per file)
            </span>
          </div>
          <span className="inline-block text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-3 py-1 rounded-full border border-emerald-500/30">
            SHA-256 Deduplication & Sentence-Boundary Chunking Active
          </span>
        </div>
      </div>

      {/* Upload Notification Message */}
      {uploadMessage && (
        <div className="rounded-xl border border-[#8B5CF6]/30 bg-[#8B5CF6]/10 p-4 text-xs font-medium text-[#F5F3FF] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>{uploadMessage}</span>
          </div>
          <button onClick={() => setUploadMessage(null)} className="text-[#9292A5] hover:text-[#F5F3FF]">
            ✕
          </button>
        </div>
      )}

      {/* Documents Table */}
      <div className="rounded-2xl border border-[#232336] bg-[#151521] overflow-hidden shadow-xl">
        <div className="p-5 border-b border-[#232336] flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider">
            All Ingested Documents ({documents.length})
          </h3>
          <span className="text-xs text-[#9292A5]">Indexed in Atlas & ChromaDB</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#101019] text-[#9292A5] uppercase font-mono tracking-wider border-b border-[#232336]">
              <tr>
                <th className="p-4">Document Name</th>
                <th className="p-4">Storage</th>
                <th className="p-4">Type</th>
                <th className="p-4">Size</th>
                <th className="p-4">Chunks</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232336] text-[#F5F3FF]">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-12 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="h-12 w-12 rounded-xl bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center">
                        <FileUp className="h-6 w-6 text-[#A78BFA]/60" />
                      </div>
                      <p className="text-sm font-semibold text-[#F5F3FF]">No documents yet</p>
                      <p className="text-xs text-[#9292A5]">Upload your first file using the area above to get started.</p>
                    </div>
                  </td>
                </tr>
              ) : (
              documents.map((doc) => {
                const isSupabase = doc.file.storage_provider === 'supabase' || !!doc.file.storage_url;
                const fileDownloadUrl = doc.file.storage_url || echoesApi.getDocumentDownloadUrl(doc.document_id);

                return (
                  <tr key={doc.document_id} className="hover:bg-[#1A1A2B] transition-colors">
                    <td className="p-4 font-semibold flex items-center gap-2.5">
                      <FileText className="h-4 w-4 text-[#A78BFA] shrink-0" />
                      <span className="truncate max-w-xs">{doc.file.original_name}</span>
                    </td>
                    <td className="p-4">
                      {isSupabase ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-[#10B981]/15 px-2 py-0.5 font-bold uppercase text-[10px] text-[#34D399] border border-[#10B981]/30">
                          <Cloud className="h-3 w-3" />
                          Supabase
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-md bg-[#232336]/60 px-2 py-0.5 font-bold uppercase text-[10px] text-[#9292A5] border border-[#232336]">
                          Local
                        </span>
                      )}
                    </td>
                    <td className="p-4 uppercase font-mono text-[#9292A5]">
                      {doc.file.file_type}
                    </td>
                    <td className="p-4 text-[#9292A5]">
                      {Math.round(doc.file.size_bytes / 1024)} KB
                    </td>
                    <td className="p-4 font-mono font-bold text-[#818CF8]">
                      {doc.processing.chunk_count}
                    </td>
                    <td className="p-4">
                      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-950/60 px-2 py-0.5 font-bold uppercase text-[10px] text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="h-3 w-3" />
                        {doc.processing.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <a
                          href={fileDownloadUrl}
                          target="_blank"
                          rel="noreferrer"
                          title="Download / View Original File"
                          className="rounded-lg border border-[#232336] bg-[#101019] p-2 text-xs font-semibold text-[#818CF8] hover:bg-[#1E1E30] hover:text-[#A78BFA] transition-colors inline-flex items-center"
                        >
                          <Download className="h-3.5 w-3.5" />
                        </a>
                        <button
                          onClick={() => inspectChunks(doc)}
                          className="rounded-lg border border-[#232336] bg-[#101019] px-2.5 py-1.5 text-xs font-semibold text-[#A78BFA] hover:bg-[#1E1E30] transition-colors inline-flex items-center gap-1.5"
                          title="View Ingested Chunks"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Chunks
                        </button>
                        <button
                          onClick={() => handleDeleteDocument(doc.document_id, doc.file.original_name)}
                          className="rounded-lg border border-red-500/20 bg-red-950/20 p-2 text-xs font-semibold text-red-400 hover:bg-red-950/50 hover:text-red-300 transition-colors inline-flex items-center"
                          title="Delete Document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Chunk Viewer Modal */}
      {selectedDocChunks && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-3xl rounded-2xl border border-[#232336] bg-[#151521] p-6 shadow-2xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-[#232336]">
              <div>
                <span className="text-[10px] font-mono text-[#A78BFA] font-bold uppercase tracking-wider">
                  Chunk Provenance Inspector
                </span>
                <h3 className="text-base font-bold text-[#F5F3FF] mt-0.5">{activeDocName}</h3>
              </div>
              <button
                onClick={() => setSelectedDocChunks(null)}
                className="text-[#9292A5] hover:text-[#F5F3FF]"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
              {selectedDocChunks.length === 0 ? (
                <p className="text-xs text-[#9292A5]">No chunks available for this file.</p>
              ) : (
                selectedDocChunks.map((c, i) => (
                  <div key={c.chunk_id || i} className="rounded-xl border border-[#232336] bg-[#101019] p-4 text-xs space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-[#A78BFA] font-mono">
                      <span>{c.chunk_id}</span>
                      <span>Page {c.page_number || 1} · {c.token_count} tokens</span>
                    </div>
                    <p className="text-[#F5F3FF] leading-relaxed font-sans">{c.text}</p>
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t border-[#232336] text-right">
              <button
                onClick={() => setSelectedDocChunks(null)}
                className="rounded-xl bg-[#1E1E30] px-4 py-2 text-xs font-semibold text-[#F5F3FF] hover:bg-[#2A2A42]"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
