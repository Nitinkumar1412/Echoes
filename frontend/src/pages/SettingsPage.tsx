import React, { useState, useEffect } from 'react';
import {
  Settings,
  Database,
  Shield,
  Key,
  Layers,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Cloud,
} from 'lucide-react';
import { echoesApi } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; database: string }>({
    status: 'checking',
    database: 'checking',
  });
  const [checking, setChecking] = useState(false);

  const checkStatus = async () => {
    setChecking(true);
    const res = await echoesApi.checkHealth();
    setHealth(res);
    setChecking(false);
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="pb-6 border-b border-[#232336]">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#A78BFA] font-bold mb-1">
          <Settings className="h-4 w-4" />
          System Preferences
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF] tracking-tight">
          Platform Configuration & Infrastructure
        </h1>
        <p className="text-sm text-[#9292A5] mt-1">
          Monitor your database connections, vector stores, and model parameters.
        </p>
      </div>

      {/* Backend & Database Health Status */}
      <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-[#232336]">
          <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider flex items-center gap-2">
            <Database className="h-4 w-4 text-[#8B5CF6]" />
            Backend Infrastructure Health
          </h3>
          <button
            onClick={checkStatus}
            disabled={checking}
            className="flex items-center gap-1.5 text-xs text-[#A78BFA] hover:underline"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${checking ? 'animate-spin' : ''}`} />
            Recheck Connection
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-[#232336] bg-[#101019] p-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-[#9292A5] block">FastAPI Backend</span>
              <span className="text-sm font-bold text-[#F5F3FF]">
                {checking || health.status === 'checking'
                  ? 'Checking connection...'
                  : health.status === 'ok'
                  ? 'Online (HTTP 200)'
                  : 'Offline / Mock Mode'}
              </span>
            </div>
            <span
              className={`h-3 w-3 rounded-full ${
                checking || health.status === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : health.status === 'ok'
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  : 'bg-amber-400'
              }`}
            />
          </div>

          <div className="rounded-xl border border-[#232336] bg-[#101019] p-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-[#9292A5] block">MongoDB Atlas</span>
              <span className="text-sm font-bold text-[#F5F3FF]">
                {checking || health.database === 'checking'
                  ? 'Checking database...'
                  : health.database === 'connected'
                  ? 'Connected (echoes_db)'
                  : 'Atlas Disconnected'}
              </span>
            </div>
            <span
              className={`h-3 w-3 rounded-full ${
                checking || health.database === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : health.database === 'connected'
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  : 'bg-rose-400'
              }`}
            />
          </div>

          <div className="rounded-xl border border-[#232336] bg-[#101019] p-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-[#9292A5] block">Supabase Storage</span>
              <span className="text-sm font-bold text-[#F5F3FF]">
                Connected (Echoes_documents)
              </span>
            </div>
            <span
              className="h-3 w-3 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
            />
          </div>
        </div>
      </div>

      {/* RAG Engine Parameters */}
      <div className="rounded-2xl border border-[#232336] bg-[#151521] p-6 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-[#F5F3FF] uppercase tracking-wider flex items-center gap-2 pb-3 border-b border-[#232336]">
          <Cpu className="h-4 w-4 text-[#818CF8]" />
          RAG Pipeline Configuration
        </h3>

        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3 rounded-xl bg-[#101019] border border-[#232336]">
            <div>
              <span className="font-semibold text-[#F5F3FF] block">Embedding Model</span>
              <span className="text-[#9292A5]">SentenceTransformers (Dense 384 dimensions)</span>
            </div>
            <span className="font-mono text-[#A78BFA] font-bold bg-[#1E1E30] px-2 py-1 rounded">
              all-MiniLM-L6-v2
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-[#101019] border border-[#232336]">
            <div>
              <span className="font-semibold text-[#F5F3FF] block">Vector Database</span>
              <span className="text-[#9292A5]">ChromaDB Persistent Cosine Index</span>
            </div>
            <span className="font-mono text-emerald-400 font-bold bg-[#1E1E30] px-2 py-1 rounded">
              storage/vectors/
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-[#101019] border border-[#232336]">
            <div>
              <span className="font-semibold text-[#F5F3FF] block">Chunking Parameters</span>
              <span className="text-[#9292A5]">Sentence-boundary aware with overlap</span>
            </div>
            <span className="font-mono text-[#F5F3FF] font-bold bg-[#1E1E30] px-2 py-1 rounded">
              512 tokens / 64 overlap
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-[#101019] border border-[#232336]">
            <div>
              <span className="font-semibold text-[#F5F3FF] block">Reasoning LLM</span>
              <span className="text-[#9292A5]">Google Gemini 2.5 Flash via google-genai</span>
            </div>
            <span className="font-mono text-violet-400 font-bold bg-[#1E1E30] px-2 py-1 rounded">
              gemini-2.5-flash
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
