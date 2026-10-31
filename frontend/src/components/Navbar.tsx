import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Compass, Network, Clock, ArrowRight } from 'lucide-react';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-[#232336] bg-[#09090F]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-[#8B5CF6] to-[#6366F1] shadow-lg shadow-[#8B5CF6]/25 transition-transform duration-300 group-hover:scale-105">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-[#F5F3FF]">
              Echoes<span className="text-[#8B5CF6]">.</span>
            </span>
          </div>
        </Link>

        {/* Links */}
        <div className="hidden md:flex items-center gap-7 text-sm font-medium text-[#9292A5]">
          <a href="#features" className="transition-colors hover:text-[#F5F3FF]">
            Features
          </a>
          <a href="#graph-preview" className="transition-colors hover:text-[#F5F3FF]">
            Memory Graph
          </a>
          <a href="#how-it-works" className="transition-colors hover:text-[#F5F3FF]">
            How It Works
          </a>
          <Link to="/app/timeline" className="transition-colors hover:text-[#F5F3FF]">
            Timeline
          </Link>
        </div>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="hidden sm:inline-flex text-sm font-medium text-[#9292A5] hover:text-[#F5F3FF] transition-colors px-3 py-1.5"
          >
            Sign In
          </Link>
          <button
            onClick={() => navigate('/app')}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#6366F1] px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-[#8B5CF6]/30 transition-all hover:brightness-110 active:scale-95"
          >
            Launch Platform
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
};
