import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  Sparkles,
  Network,
  Clock,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  RotateCcw,
  BookOpen,
  Share2,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import type { QueryResult, Citation } from '../types';
import { CitationModal } from '../components/CitationModal';

export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const [error, setError] = useState<string | null>(null);

  const sampleSuggestions = [
    'What decisions did I make last month?',
    'Summarize the key topics from my documents',
    'What meetings have I had recently?',
    'Show me all milestones and deadlines',
  ];

  const executeSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await echoesApi.askQuestion(searchQuery.trim());
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const qParam = searchParams.get('q');
    if (qParam) {
      setQuery(qParam);
      executeSearch(qParam);
    }
  }, [searchParams]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
      executeSearch(query.trim());
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      {/* Header Search Box */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#A78BFA] font-bold">
            <Sparkles className="h-4 w-4" />
            Evidence-Grounded AI Search
          </div>
          {result && result.performance && (
            <span className="text-xs text-[#9292A5] font-mono">
              Total: {result.performance.total_ms}ms (Retrieval: {result.performance.retrieval_ms}ms)
            </span>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="relative flex items-center rounded-2xl border border-[#232336] bg-[#151521] p-3 shadow-2xl shadow-black/60 focus-within:border-[#8B5CF6] focus-within:ring-4 focus-within:ring-[#8B5CF6]/20 transition-all">
            <Search className="h-5 w-5 text-[#9292A5] ml-2 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask any question about your past documents, notes, decisions, or timeline..."
              className="w-full bg-transparent px-3 py-1 text-base text-[#F5F3FF] placeholder-[#64647A] focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex items-center gap-2 rounded-xl bg-[#8B5CF6] px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-[#8B5CF6]/30 hover:bg-[#7C3AED] transition-all disabled:opacity-50 shrink-0"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  Ask Echoes
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Suggestion Chips */}
        {!result && !loading && (
          <div className="space-y-2 pt-2">
            <span className="text-xs font-semibold text-[#9292A5]">Suggested questions from your memories:</span>
            <div className="flex flex-wrap gap-2">
              {sampleSuggestions.map((sug, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuery(sug);
                    setSearchParams({ q: sug });
                    executeSearch(sug);
                  }}
                  className="rounded-xl border border-[#232336] bg-[#101019] px-3.5 py-2 text-xs text-[#9292A5] hover:text-[#F5F3FF] hover:border-[#8B5CF6]/40 hover:bg-[#151521] transition-all text-left"
                >
                  "{sug}"
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="rounded-2xl border border-[#232336] bg-[#151521] p-8 space-y-4 animate-pulse">
          <div className="h-5 w-1/3 bg-[#1E1E30] rounded-md" />
          <div className="h-4 w-full bg-[#1E1E30] rounded-md" />
          <div className="h-4 w-5/6 bg-[#1E1E30] rounded-md" />
          <div className="h-4 w-4/6 bg-[#1E1E30] rounded-md" />
          <div className="pt-6 grid grid-cols-3 gap-4">
            <div className="h-20 bg-[#101019] rounded-xl border border-[#232336]" />
            <div className="h-20 bg-[#101019] rounded-xl border border-[#232336]" />
            <div className="h-20 bg-[#101019] rounded-xl border border-[#232336]" />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="rounded-2xl border border-red-500/30 bg-red-950/20 p-6 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-red-300">Search failed</p>
            <p className="text-xs text-red-400/80 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Search Result */}
      {result && !loading && (
        <div className="space-y-8 animate-in fade-in duration-300">
          {/* Main Answer Card */}
          <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6 sm:p-8 shadow-xl relative overflow-hidden">
            {/* Top metadata row */}
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-[#232336]">
              <div className="flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                <span className="text-xs font-bold text-[#F5F3FF]">Grounded Synthesis</span>
                <span className="text-xs text-[#9292A5]">· Gemini 2.5 Flash</span>
              </div>

              {/* Confidence Badge */}
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border ${
                    result.confidence === 'high'
                      ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30'
                      : result.confidence === 'medium'
                      ? 'bg-indigo-950/60 text-indigo-400 border-indigo-500/30'
                      : 'bg-amber-950/60 text-amber-400 border-amber-500/30'
                  }`}
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Confidence: {result.confidence}
                </span>
              </div>
            </div>

            {/* Answer Body */}
            <div className="prose prose-invert max-w-none text-base leading-relaxed text-[#F5F3FF] font-sans">
              <p className="whitespace-pre-line">{result.answer}</p>
            </div>

            {/* Bottom Actions Row */}
            <div className="flex flex-wrap items-center justify-between gap-4 mt-8 pt-6 border-t border-[#232336]">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate('/app/graph')}
                  className="flex items-center gap-2 rounded-xl bg-[#8B5CF6]/15 hover:bg-[#8B5CF6]/25 text-[#A78BFA] border border-[#8B5CF6]/30 px-3.5 py-2 text-xs font-semibold transition-all"
                >
                  <Network className="h-4 w-4" />
                  Explore in Memory Graph
                </button>
                <button
                  onClick={() => navigate('/app/timeline')}
                  className="flex items-center gap-2 rounded-xl bg-[#1E1E30] hover:bg-[#2A2A42] text-[#F5F3FF] border border-[#232336] px-3.5 py-2 text-xs font-semibold transition-all"
                >
                  <Clock className="h-4 w-4" />
                  Reconstruct on Timeline
                </button>
              </div>

              <span className="text-xs text-[#64647A]">Verified with ChromaDB & Atlas</span>
            </div>
          </div>

          {/* Source Citations Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider flex items-center gap-2">
                <FileText className="h-4 w-4 text-[#8B5CF6]" />
                Underlying Source Citations ({result.citations.length})
              </h3>
              <span className="text-xs text-[#9292A5]">Click any citation to inspect raw chunk</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {result.citations.map((cite, idx) => (
                <div
                  key={cite.chunk_id || idx}
                  onClick={() => setActiveCitation(cite)}
                  className="group rounded-xl border border-[#232336] bg-[#101019] hover:bg-[#151521] hover:border-[#8B5CF6]/50 p-4 transition-all cursor-pointer shadow-md flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="font-semibold text-[#A78BFA] flex items-center gap-1.5 truncate">
                        <FileText className="h-3.5 w-3.5 shrink-0" />
                        {cite.document_name}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 font-bold">
                        {Math.round(cite.relevance_score * 100)}% match
                      </span>
                    </div>
                    <p className="text-xs text-[#9292A5] line-clamp-3 leading-relaxed">
                      "{cite.excerpt}"
                    </p>
                  </div>
                  <div className="pt-3 border-t border-[#1F1F2E] mt-3 flex items-center justify-between text-[10px] text-[#64647A]">
                    <span className="font-mono">{cite.chunk_id}</span>
                    <span className="text-[#8B5CF6] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      Inspect <ExternalLink className="h-3 w-3" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Related Timeline Events Section (if any found) */}
          {result.timeline && result.timeline.length > 0 && (
            <div className="rounded-2xl border border-[#232336] bg-[#101019] p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#232336]">
                <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-400" />
                  Chronological Context
                </h3>
                <button
                  onClick={() => navigate('/app/timeline')}
                  className="text-xs text-[#A78BFA] hover:underline"
                >
                  View Full Timeline
                </button>
              </div>

              <div className="space-y-3">
                {result.timeline.map((ev, i) => (
                  <div key={ev.event_id || i} className="flex items-start gap-3 text-xs">
                    <span className="rounded-md bg-[#1E1E30] text-[#A78BFA] font-mono px-2 py-0.5 shrink-0">
                      {ev.original_expression || 'Date anchor'}
                    </span>
                    <span className="text-[#F5F3FF] font-medium">{ev.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Citation Inspector Modal */}
      <CitationModal citation={activeCitation} onClose={() => setActiveCitation(null)} />
    </div>
  );
};
