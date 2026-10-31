import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Search,
  Calendar,
  Sparkles,
  FileText,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import type { QueryResult } from '../types';

export const LibraryPage: React.FC = () => {
  const navigate = useNavigate();
  const [queries, setQueries] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedConfidence, setSelectedConfidence] = useState('ALL');

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await echoesApi.getQueryHistory();
      setQueries(data);
    } catch (e) {
      console.error('Failed to load query history:', e);
      setQueries([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const confidenceOptions = ['ALL', 'high', 'medium', 'low'];

  const filtered = queries.filter((q) => {
    const matchConf = selectedConfidence === 'ALL' || q.confidence === selectedConfidence;
    const matchSearch =
      q.query.toLowerCase().includes(search.toLowerCase()) ||
      q.answer.toLowerCase().includes(search.toLowerCase()) ||
      (q.citations && q.citations.some((c) => c.document_name.toLowerCase().includes(search.toLowerCase())));
    return matchConf && matchSearch;
  });

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-[#232336]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#A78BFA] font-bold mb-1">
            <BookOpen className="h-4 w-4" />
            Curated Knowledge Base
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF] tracking-tight">
            Memory & Query Library
          </h1>
          <p className="text-sm text-[#9292A5] mt-1">
            Browse discovered answers, evidence citations, and past synthesis queries.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Refresh */}
          <button
            onClick={fetchHistory}
            className="flex items-center gap-1.5 rounded-xl bg-[#151521] border border-[#232336] px-3.5 py-2 text-xs font-semibold text-[#9292A5] hover:text-[#F5F3FF]"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="h-4 w-4 text-[#9292A5] ml-3.5 absolute top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search queries, answers, or referenced documents..."
            className="w-full rounded-xl border border-[#232336] bg-[#151521] pl-10 pr-4 py-2.5 text-xs sm:text-sm text-[#F5F3FF] placeholder-[#64647A] focus:outline-none focus:border-[#8B5CF6]"
          />
        </div>

        <div className="flex items-center gap-1 bg-[#101019] p-1 rounded-xl border border-[#232336]">
          {confidenceOptions.map((conf) => (
            <button
              key={conf}
              onClick={() => setSelectedConfidence(conf)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                selectedConfidence === conf
                  ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/30'
                  : 'text-[#9292A5] hover:text-[#F5F3FF]'
              }`}
            >
              {conf}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center p-16">
          <RefreshCw className="h-6 w-6 text-[#A78BFA] animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-3xl border border-[#232336] bg-[#151521] p-12 text-center flex flex-col items-center gap-3">
          <div className="h-12 w-12 rounded-2xl bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center">
            <BookOpen className="h-6 w-6 text-[#A78BFA]" />
          </div>
          <h3 className="text-base font-bold text-[#F5F3FF]">No memories or queries found</h3>
          <p className="text-xs text-[#9292A5] max-w-sm">
            {search
              ? 'No queries match your search filter. Try different terms or clear the filter.'
              : 'Ask questions in the Search tab or upload documents in Sources to build your evidence-grounded memory bank.'}
          </p>
          <button
            onClick={() => navigate('/app/search')}
            className="mt-2 inline-flex items-center gap-2 rounded-xl bg-[#8B5CF6] px-4 py-2 text-xs font-semibold text-white hover:bg-[#7C3AED] transition-colors"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Go to Search & Ask AI
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filtered.map((item) => {
            const dateStr = item.created_at
              ? new Date(item.created_at).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })
              : 'Recent';

            return (
              <div
                key={item.query_id}
                className="rounded-2xl border border-[#232336] bg-[#151521] p-6 hover:border-[#8B5CF6]/40 transition-all shadow-lg flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs mb-3">
                    <span
                      className={`font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border text-[10px] ${
                        item.confidence === 'high'
                          ? 'bg-emerald-950/40 text-emerald-400 border-emerald-500/30'
                          : item.confidence === 'medium'
                          ? 'bg-amber-950/40 text-amber-400 border-amber-500/30'
                          : 'bg-rose-950/40 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {item.confidence} confidence
                    </span>
                    <span className="text-[#9292A5] flex items-center gap-1 text-[11px]">
                      <Calendar className="h-3.5 w-3.5" />
                      {dateStr}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-[#F5F3FF] mb-2 flex items-start gap-2">
                    <span className="text-[#8B5CF6]">Q:</span>
                    <span>{item.query}</span>
                  </h3>
                  <p className="text-xs text-[#9292A5] leading-relaxed line-clamp-3 mb-4">
                    {item.answer}
                  </p>
                </div>

                <div>
                  {item.citations && item.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {item.citations.slice(0, 3).map((cit) => (
                        <span
                          key={cit.chunk_id}
                          className="text-[10px] text-[#A78BFA] bg-[#101019] border border-[#232336] px-2 py-0.5 rounded-md flex items-center gap-1"
                        >
                          <FileText className="h-3 w-3" />
                          {cit.document_name}
                        </span>
                      ))}
                      {item.citations.length > 3 && (
                        <span className="text-[10px] text-[#9292A5] px-1 py-0.5">
                          +{item.citations.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-[#1F1F2E] text-xs">
                    <span className="text-[#64647A] flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      {item.performance?.total_ms ? `${item.performance.total_ms}ms` : 'Analyzed'}
                    </span>
                    <button
                      onClick={() => navigate(`/app/search?q=${encodeURIComponent(item.query)}`)}
                      className="text-[#8B5CF6] hover:text-[#A78BFA] font-semibold flex items-center gap-1 transition-colors"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      Ask Again
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
