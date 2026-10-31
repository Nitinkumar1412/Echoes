import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Sparkles,
  Network,
  Clock,
  FileText,
  Brain,
  Layers,
  ArrowRight,
  TrendingUp,
  FolderGit2,
  Calendar,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import type { DocumentItem, TimelineItem, QueryResult } from '../types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [queryInput, setQueryInput] = useState('');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineItem[]>([]);
  const [recentQueries, setRecentQueries] = useState<QueryResult[]>([]);
  const [entityCount, setEntityCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      echoesApi.getDocuments(),
      echoesApi.getTimeline(),
      echoesApi.getQueryHistory(),
      echoesApi.listEntities(),
    ]).then(([docs, events, queries, entitiesRes]) => {
      setDocuments(docs);
      setTimelineEvents(events);
      setRecentQueries(queries);
      setEntityCount(entitiesRes?.total_entities ?? entitiesRes?.entities?.length ?? 0);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (queryInput.trim()) {
      navigate(`/app/search?q=${encodeURIComponent(queryInput.trim())}`);
    }
  };

  const totalChunks = documents.reduce((acc, d) => acc + (d.processing?.chunk_count || 0), 0);

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-[#232336]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF] tracking-tight">
            Memory Workspace Overview
          </h1>
          <p className="text-sm text-[#9292A5] mt-1">
            Reconstruct memories, search connected knowledge, and explore chronological events.
          </p>
        </div>

        <button
          onClick={() => navigate('/app/sources')}
          className="flex items-center gap-2 rounded-xl bg-[#1E1E30] hover:bg-[#2A2A42] text-[#F5F3FF] border border-[#232336] px-4 py-2.5 text-xs font-semibold transition-all"
        >
          <FolderGit2 className="h-4 w-4 text-[#A78BFA]" />
          Upload New Document
        </button>
      </div>

      {/* Global Quick Search Bar */}
      <form onSubmit={handleSearchSubmit}>
        <div className="relative flex items-center rounded-2xl border border-[#232336] bg-[#151521] p-2 shadow-xl shadow-black/40 focus-within:border-[#8B5CF6] focus-within:ring-4 focus-within:ring-[#8B5CF6]/15 transition-all">
          <Search className="h-5 w-5 text-[#9292A5] ml-3 shrink-0" />
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Ask anything about your past memories, projects, or documents..."
            className="w-full bg-transparent px-3 py-2 text-sm text-[#F5F3FF] placeholder-[#64647A] focus:outline-none"
          />
          <button
            type="submit"
            className="flex items-center gap-2 rounded-xl bg-[#8B5CF6] px-4 py-2 text-xs font-semibold text-white shadow-md shadow-[#8B5CF6]/20 hover:bg-[#7C3AED] transition-all"
          >
            Ask Echoes
            <Sparkles className="h-3.5 w-3.5" />
          </button>
        </div>
      </form>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5">
          <div className="flex items-center justify-between text-[#9292A5] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Indexed Documents</span>
            <FileText className="h-4 w-4 text-[#A78BFA]" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF]">
            {loading ? '—' : documents.length}
          </div>
          <span className="text-[11px] text-[#64647A] mt-1 block">PDFs, DOCX, & Markdown</span>
        </div>

        <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5">
          <div className="flex items-center justify-between text-[#9292A5] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Vector Chunks</span>
            <Layers className="h-4 w-4 text-[#818CF8]" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF]">
            {loading ? '—' : totalChunks}
          </div>
          <span className="text-[11px] text-[#64647A] mt-1 block">ChromaDB Cosine Index</span>
        </div>

        <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5">
          <div className="flex items-center justify-between text-[#9292A5] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Graph Entities</span>
            <Network className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF]">
            {loading ? '—' : entityCount}
          </div>
          <span className="text-[11px] text-[#64647A] mt-1 block">NetworkX Multi-Hop</span>
        </div>

        <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5">
          <div className="flex items-center justify-between text-[#9292A5] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Timeline Events</span>
            <Clock className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF]">
            {loading ? '—' : timelineEvents.length}
          </div>
          <span className="text-[11px] text-[#64647A] mt-1 block">Normalized ISO Timestamps</span>
        </div>
      </div>

      {/* Quick Launch Showcase: Memory Graph & Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Memory Graph Card */}
        <div
          onClick={() => navigate('/app/graph')}
          className="group rounded-2xl border border-[#232336] bg-gradient-to-br from-[#151521] to-[#12121E] p-6 cursor-pointer hover:border-[#8B5CF6]/50 transition-all shadow-xl hover:shadow-[#8B5CF6]/10"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-950/60 text-[#A78BFA] border border-violet-500/30">
              <Network className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold text-[#8B5CF6] group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
              Explore Graph <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </div>
          <h3 className="text-lg font-bold text-[#F5F3FF] mb-1.5">Interactive Knowledge Graph</h3>
          <p className="text-xs text-[#9292A5] leading-relaxed">
            Explore interconnected entities, collaborators, organizations, and projects extracted from your documents.
          </p>
        </div>

        {/* Temporal Reconstruction Card */}
        <div
          onClick={() => navigate('/app/timeline')}
          className="group rounded-2xl border border-[#232336] bg-gradient-to-br from-[#151521] to-[#12121E] p-6 cursor-pointer hover:border-[#6366F1]/50 transition-all shadow-xl hover:shadow-[#6366F1]/10"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-950/60 text-[#818CF8] border border-indigo-500/30">
              <Clock className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold text-[#818CF8] group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
              View Timeline <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </div>
          <h3 className="text-lg font-bold text-[#F5F3FF] mb-1.5">Temporal Timeline</h3>
          <p className="text-xs text-[#9292A5] leading-relaxed">
            Reconstruct historical sequences from dates, meeting milestones, and decisions across your knowledge bank.
          </p>
        </div>
      </div>

      {/* Recent Discovered Memories & Ingested Files */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Ingested Files */}
        <div className="lg:col-span-2 rounded-2xl border border-[#232336] bg-[#151521] p-6">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#232336]">
            <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider">
              Ingested Knowledge Sources
            </h3>
            <button
              onClick={() => navigate('/app/sources')}
              className="text-xs text-[#A78BFA] hover:underline"
            >
              View All
            </button>
          </div>

          <div className="space-y-3">
            {documents.length === 0 ? (
              <div className="py-8 text-center text-xs text-[#9292A5] flex flex-col items-center gap-2">
                <FileText className="h-6 w-6 text-[#9292A5]/40" />
                <span>No documents ingested yet.</span>
              </div>
            ) : (
              documents.slice(0, 4).map((doc) => (
                <div
                  key={doc.document_id}
                  onClick={() => navigate('/app/sources')}
                  className="flex items-center justify-between p-3 rounded-xl bg-[#101019] hover:bg-[#1A1A2B] border border-[#232336] transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-[#1E1E30] text-[#A78BFA]">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-[#F5F3FF]">{doc.file.original_name}</h4>
                      <span className="text-[10px] text-[#9292A5]">
                        {doc.processing.chunk_count} chunks · {Math.round(doc.file.size_bytes / 1024)} KB
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-md border border-emerald-500/30">
                    {doc.processing.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Queries */}
        <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#232336]">
            <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider">
              Recent Inquiries
            </h3>
            <Sparkles className="h-4 w-4 text-[#A78BFA]" />
          </div>

          <div className="space-y-3">
            {recentQueries.length === 0 ? (
              <div className="py-8 text-center text-xs text-[#9292A5] flex flex-col items-center gap-2">
                <Sparkles className="h-6 w-6 text-[#9292A5]/40" />
                <span>No queries asked yet. Ask a question above!</span>
              </div>
            ) : (
              recentQueries.slice(0, 3).map((q, i) => (
                <div
                  key={q.query_id || i}
                  onClick={() => navigate(`/app/search?q=${encodeURIComponent(q.query)}`)}
                  className="p-3 rounded-xl bg-[#101019] hover:bg-[#1A1A2B] border border-[#232336] transition-colors cursor-pointer"
                >
                  <span className="text-xs text-[#F5F3FF] font-medium block truncate">
                    "{q.query}"
                  </span>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-[#A78BFA] font-bold uppercase">
                      {q.confidence}
                    </span>
                    <span className="text-[10px] text-[#64647A]">
                      · {q.citations?.length || 0} citations
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
