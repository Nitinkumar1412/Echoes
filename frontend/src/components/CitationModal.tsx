import React from 'react';
import { X, FileText, CheckCircle2, ExternalLink, Network, Copy, Check } from 'lucide-react';
import type { Citation } from '../types';
import { useNavigate } from 'react-router-dom';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  const navigate = useNavigate();
  const [copied, setCopied] = React.useState(false);

  if (!citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(`"${citation.excerpt}" — Source: ${citation.document_name}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl rounded-2xl border border-[#232336] bg-[#151521] p-6 shadow-2xl shadow-black/80">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-[#232336]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8B5CF6]/15 text-[#A78BFA] border border-[#8B5CF6]/30">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-[#F5F3FF] text-base">{citation.document_name}</h3>
              <p className="text-xs text-[#9292A5] font-mono">{citation.chunk_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-[#9292A5] hover:bg-[#1E1E30] hover:text-[#F5F3FF] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="py-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-[#9292A5] uppercase tracking-wider block mb-2">
              Verified Chunk Evidence Excerpt
            </label>
            <div className="rounded-xl border border-[#8B5CF6]/20 bg-[#09090F]/70 p-4 text-sm leading-relaxed text-[#F5F3FF] font-sans selection:bg-[#8B5CF6]/40">
              "{citation.excerpt}"
            </div>
          </div>

          {/* Relevance Score Indicator */}
          <div className="rounded-xl bg-[#101019] p-3 border border-[#232336] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span className="text-xs text-[#9292A5]">Hybrid Retrieval Relevance</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-24 bg-[#1E1E30] h-2 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] h-full rounded-full"
                  style={{ width: `${Math.round(citation.relevance_score * 100)}%` }}
                />
              </div>
              <span className="text-xs font-mono font-bold text-[#A78BFA]">
                {Math.round(citation.relevance_score * 100)}%
              </span>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#232336]">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-xl border border-[#232336] bg-[#1E1E30] px-3.5 py-2 text-xs font-medium text-[#F5F3FF] hover:bg-[#2A2A42] transition-colors"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied Citation' : 'Copy Quote'}
          </button>
          <button
            onClick={() => {
              onClose();
              navigate('/app/graph');
            }}
            className="flex items-center gap-1.5 rounded-xl bg-[#8B5CF6] px-4 py-2 text-xs font-semibold text-white shadow-md shadow-[#8B5CF6]/30 hover:bg-[#7C3AED] transition-all"
          >
            <Network className="h-3.5 w-3.5" />
            Explore in Memory Graph
          </button>
        </div>
      </div>
    </div>
  );
};
