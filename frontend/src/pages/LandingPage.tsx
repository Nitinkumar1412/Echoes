import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Search,
  Network,
  Clock,
  Layers,
  ShieldCheck,
  ArrowRight,
  Database,
  Brain,
  FileCheck2,
  ChevronRight,
} from 'lucide-react';
import { Navbar } from '../components/Navbar';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [heroQuery, setHeroQuery] = useState('');

  const handleHeroSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (heroQuery.trim()) {
      navigate(`/app/search?q=${encodeURIComponent(heroQuery.trim())}`);
    } else {
      navigate('/app/search');
    }
  };

  return (
    <div className="min-h-screen bg-[#09090F] text-[#F5F3FF] selection:bg-[#8B5CF6]/40">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-28 md:pt-32 md:pb-36">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[#8B5CF6]/15 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-1/3 left-1/3 w-[300px] h-[250px] bg-[#6366F1]/10 blur-[90px] rounded-full pointer-events-none" />

        <div className="relative mx-auto max-w-5xl px-6 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-[#8B5CF6]/30 bg-[#8B5CF6]/10 px-4 py-1.5 text-xs font-semibold text-[#A78BFA] mb-8 shadow-sm shadow-[#8B5CF6]/20">
            <Sparkles className="h-3.5 w-3.5" />
            Track 2 RAG Engine — MongoDB Atlas & ChromaDB Powered
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-[#F5F3FF] leading-[1.1] mb-6">
            Your past has more connections <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-[#A78BFA] via-[#C084FC] to-[#818CF8] bg-clip-text text-transparent">
              than you remember.
            </span>
          </h1>

          {/* Supporting Text */}
          <p className="mx-auto max-w-2xl text-base sm:text-lg text-[#9292A5] leading-relaxed mb-10">
            Search across your notes, documents, transcripts, and conversations. Uncover hidden
            connections through an interconnected knowledge graph and reconstruct your personal timeline with
            provable AI citations.
          </p>

          {/* Search Box Preview */}
          <form onSubmit={handleHeroSearch} className="mx-auto max-w-2xl mb-10">
            <div className="relative flex items-center rounded-2xl border border-[#232336] bg-[#151521]/90 backdrop-blur-xl p-2 shadow-2xl shadow-black/80 transition-all focus-within:border-[#8B5CF6] focus-within:ring-4 focus-within:ring-[#8B5CF6]/20">
              <Search className="h-5 w-5 text-[#9292A5] ml-3 shrink-0" />
              <input
                type="text"
                value={heroQuery}
                onChange={(e) => setHeroQuery(e.target.value)}
                placeholder="Ask about your past: 'When did I discuss our startup architecture?'"
                className="w-full bg-transparent px-3 py-2 text-sm sm:text-base text-[#F5F3FF] placeholder-[#64647A] focus:outline-none"
              />
              <button
                type="submit"
                className="flex items-center gap-2 rounded-xl bg-[#8B5CF6] px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#8B5CF6]/30 hover:bg-[#7C3AED] transition-all active:scale-95 shrink-0"
              >
                Search
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>

          {/* CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => navigate('/app/search')}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#6366F1] px-6 py-3.5 text-sm font-semibold text-white shadow-xl shadow-[#8B5CF6]/25 hover:opacity-95 transition-all active:scale-95"
            >
              Explore Your Memories
              <ArrowRight className="h-4 w-4" />
            </button>
            <a
              href="#how-it-works"
              className="flex items-center gap-2 rounded-xl border border-[#232336] bg-[#101019] px-6 py-3.5 text-sm font-semibold text-[#F5F3FF] hover:bg-[#151521] hover:border-[#3D3D5C] transition-all"
            >
              See How It Works
            </a>
          </div>
        </div>
      </section>

      {/* Mini Product Preview: Miniature Memory Graph & Timeline Preview */}
      <section id="graph-preview" className="relative mx-auto max-w-6xl px-6 pb-28">
        <div className="rounded-3xl border border-[#232336] bg-[#101019] p-6 md:p-8 shadow-2xl relative overflow-hidden">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8 pb-6 border-b border-[#232336]">
            <div>
              <span className="text-xs font-mono uppercase text-[#A78BFA] tracking-wider font-bold">
                Interactive Architecture
              </span>
              <h2 className="text-2xl md:text-3xl font-bold text-[#F5F3FF] mt-1">
                Multi-Hop Memory Graph & Temporal Reconstruction
              </h2>
            </div>
            <button
              onClick={() => navigate('/app/graph')}
              className="flex items-center gap-2 rounded-xl border border-[#8B5CF6]/40 bg-[#8B5CF6]/10 px-4 py-2 text-xs font-semibold text-[#A78BFA] hover:bg-[#8B5CF6]/20 transition-all"
            >
              Open Full Interactive Graph
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Connected Graph Simulation Preview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5 hover:border-[#8B5CF6]/40 transition-colors">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-xl bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">
                  <Brain className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-[#F5F3FF]">Entity Extraction</h3>
                  <span className="text-xs text-[#9292A5]">RapidFuzz Deduplication</span>
                </div>
              </div>
              <p className="text-xs text-[#9292A5] leading-relaxed">
                Extracts People, Projects, Organizations, and Concepts across documents and deduplicates them into persistent canonical memory nodes.
              </p>
            </div>

            <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5 hover:border-[#8B5CF6]/40 transition-colors">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-xl bg-violet-950/60 text-violet-400 border border-violet-500/30">
                  <Network className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-[#F5F3FF]">NetworkX Knowledge Graph</h3>
                  <span className="text-xs text-[#9292A5]">Evidence-Backed Edges</span>
                </div>
              </div>
              <p className="text-xs text-[#9292A5] leading-relaxed">
                Discovers relationships like <code className="text-[#A78BFA]">WORKED_ON</code> and <code className="text-[#A78BFA]">MANAGES</code> with exact sentence citations stored in MongoDB.
              </p>
            </div>

            <div className="rounded-2xl border border-[#232336] bg-[#151521] p-5 hover:border-[#8B5CF6]/40 transition-colors">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-xl bg-indigo-950/60 text-indigo-400 border border-indigo-500/30">
                  <Clock className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-[#F5F3FF]">Temporal Timeline</h3>
                  <span className="text-xs text-[#9292A5]">ISO Date Normalization</span>
                </div>
              </div>
              <p className="text-xs text-[#9292A5] leading-relaxed">
                Reconstructs events chronologically with dateparser, categorizing milestones, meetings, and decisions in sequence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Showcase */}
      <section id="features" className="py-24 border-t border-[#232336]">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-mono uppercase text-[#A78BFA] tracking-wider font-bold">
              Core Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F5F3FF] mt-2 mb-4">
              Designed for provable memory reconstruction.
            </h2>
            <p className="text-[#9292A5] text-sm sm:text-base">
              Unlike generic chatbots that guess facts, Echoes combines lexical BM25 matching, ChromaDB dense vectors, and a NetworkX knowledge graph.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="rounded-2xl border border-[#232336] bg-[#101019] p-7 hover:border-[#3D3D5C] transition-all">
              <div className="h-12 w-12 rounded-xl bg-[#8B5CF6]/15 flex items-center justify-center text-[#A78BFA] mb-6 border border-[#8B5CF6]/30">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F3FF] mb-2.5">1. Search Across Everything</h3>
              <p className="text-sm text-[#9292A5] leading-relaxed">
                Upload PDFs, Word docs, Markdown, text files, and screenshot images. Hybrid Reciprocal Rank Fusion merges exact keywords with semantic meaning.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl border border-[#232336] bg-[#101019] p-7 hover:border-[#3D3D5C] transition-all">
              <div className="h-12 w-12 rounded-xl bg-[#6366F1]/15 flex items-center justify-center text-[#818CF8] mb-6 border border-[#6366F1]/30">
                <Network className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F3FF] mb-2.5">2. Discover Your Memory Graph</h3>
              <p className="text-sm text-[#9292A5] leading-relaxed">
                Explore multi-hop relationships. Understand how a person mentioned in a meeting memo connects to a technical decision six months later.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl border border-[#232336] bg-[#101019] p-7 hover:border-[#3D3D5C] transition-all">
              <div className="h-12 w-12 rounded-xl bg-emerald-500/15 flex items-center justify-center text-emerald-400 mb-6 border border-emerald-500/30">
                <Clock className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F3FF] mb-2.5">3. Reconstruct Your Timeline</h3>
              <p className="text-sm text-[#9292A5] leading-relaxed">
                Step through your personal history by month and year. Click on any event to see the exact paragraph where it occurred.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 border-t border-[#232336] bg-[#0B0B14]">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-mono uppercase text-[#A78BFA] tracking-wider font-bold">
              Simple 3-Step Process
            </span>
            <h2 className="text-3xl font-extrabold text-[#F5F3FF] mt-2">
              From raw documents to connected memories
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6 relative">
              <span className="text-4xl font-black text-[#232336] absolute top-4 right-4">01</span>
              <h3 className="text-base font-bold text-[#F5F3FF] mb-2">Import Your Sources</h3>
              <p className="text-xs text-[#9292A5] leading-relaxed">
                Drag and drop your notes, PDFs, or conversations. SHA-256 deduplication protects your storage from duplicate uploads.
              </p>
            </div>

            <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6 relative">
              <span className="text-4xl font-black text-[#232336] absolute top-4 right-4">02</span>
              <h3 className="text-base font-bold text-[#F5F3FF] mb-2">AI Connects the Dots</h3>
              <p className="text-xs text-[#9292A5] leading-relaxed">
                Our pipeline chunks text boundary-aware, vectors embeddings in ChromaDB, and extracts entities and dates into MongoDB.
              </p>
            </div>

            <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6 relative">
              <span className="text-4xl font-black text-[#232336] absolute top-4 right-4">03</span>
              <h3 className="text-base font-bold text-[#F5F3FF] mb-2">Search with Grounded Citations</h3>
              <p className="text-xs text-[#9292A5] leading-relaxed">
                Ask questions in natural language. Every answer is grounded with clickable citations and interactive graph connections.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="py-24 border-t border-[#232336] text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#8B5CF6]/5 to-transparent pointer-events-none" />
        <div className="relative mx-auto max-w-4xl px-6">
          <h2 className="text-3xl sm:text-5xl font-extrabold text-[#F5F3FF] mb-4">
            Your memories are waiting to be rediscovered.
          </h2>
          <p className="text-[#9292A5] text-base mb-8 max-w-xl mx-auto">
            Experience the RAG engine built for memory reconstruction. Grounded answers, knowledge graphs, and chronological timelines.
          </p>
          <button
            onClick={() => navigate('/app/search')}
            className="rounded-xl bg-[#8B5CF6] px-8 py-4 text-base font-bold text-white shadow-xl shadow-[#8B5CF6]/30 hover:bg-[#7C3AED] transition-all active:scale-95"
          >
            Launch Platform Now
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#232336] py-10 bg-[#07070C]">
        <div className="mx-auto max-w-6xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#64647A]">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[#8B5CF6]" />
            <span className="font-semibold text-[#F5F3FF]">Echoes Search</span>
            <span>— Track 2 RAG Engine</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="hover:text-[#F5F3FF] cursor-pointer">Architecture</span>
            <span className="hover:text-[#F5F3FF] cursor-pointer">Documentation</span>
            <span className="hover:text-[#F5F3FF] cursor-pointer">FastAPI + MongoDB Atlas</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
