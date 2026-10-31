import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock,
  Calendar,
  Search,
  Filter,
  CheckCircle2,
  Users,
  FileText,
  Network,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import type { TimelineItem } from '../types';

export const TimelinePage: React.FC = () => {
  const navigate = useNavigate();
  const [events, setEvents] = useState<TimelineItem[]>([]);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedEvent, setSelectedEvent] = useState<TimelineItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    echoesApi.getTimeline().then((data) => {
      setEvents(data);
      setLoading(false);
    });
  }, []);

  const filteredEvents = events.filter((ev) => {
    const matchesType = filterType === 'ALL' || ev.event_type === filterType;
    const matchesSearch =
      ev.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (ev.original_expression || '').toLowerCase().includes(searchFilter.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-[#232336]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-amber-400 font-bold mb-1">
            <Clock className="h-4 w-4" />
            Temporal Reconstruction
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F3FF] tracking-tight">
            Chronological Memory Sequence
          </h1>
          <p className="text-sm text-[#9292A5] mt-1">
            Reconstruct past milestones, decision points, and meetings extracted across all documents.
          </p>
        </div>

        {/* Filter Badges */}
        <div className="flex items-center gap-1.5 bg-[#101019] p-1.5 rounded-xl border border-[#232336]">
          {['ALL', 'MILESTONE', 'DECISION', 'MEETING', 'TASK'].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                filterType === type
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                  : 'text-[#9292A5] hover:text-[#F5F3FF]'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input Filter */}
      <div className="relative flex items-center">
        <Search className="h-4 w-4 text-[#9292A5] ml-3.5 absolute pointer-events-none" />
        <input
          type="text"
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          placeholder="Filter events by keyword or month (e.g. 'October', 'launch', 'budget')..."
          className="w-full rounded-xl border border-[#232336] bg-[#151521] pl-10 pr-4 py-2.5 text-sm text-[#F5F3FF] placeholder-[#64647A] focus:outline-none focus:border-amber-400/50"
        />
      </div>

      {/* Timeline Stream */}
      {loading ? (
        <div className="space-y-4 my-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-2xl border border-[#232336] bg-[#151521] p-5 animate-pulse space-y-3">
              <div className="h-4 w-1/4 bg-[#1E1E30] rounded-md" />
              <div className="h-5 w-3/4 bg-[#1E1E30] rounded-md" />
            </div>
          ))}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
          <div className="h-16 w-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Clock className="h-8 w-8 text-amber-400/60" />
          </div>
          <div>
            <p className="text-base font-bold text-[#F5F3FF]">No timeline events yet</p>
            <p className="text-sm text-[#9292A5] mt-1 max-w-sm">
              Upload documents and Echoes will automatically extract and reconstruct a chronological timeline from them.
            </p>
          </div>
        </div>
      ) : (
      <div className="relative pl-6 sm:pl-8 border-l-2 border-[#232336] space-y-8 my-6">
        {filteredEvents.map((ev, idx) => (
          <div key={ev.event_id || idx} className="relative group">
            {/* Timeline Dot Indicator */}
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#09090F] border-2 border-amber-400 group-hover:scale-125 transition-transform shadow-[0_0_10px_rgba(251,191,36,0.5)]" />

            {/* Event Card */}
            <div
              onClick={() => setSelectedEvent(ev)}
              className="rounded-2xl border border-[#232336] bg-[#151521] p-5 hover:bg-[#1A1A2B] hover:border-amber-400/40 transition-all cursor-pointer shadow-lg"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-bold text-amber-300 bg-amber-950/60 border border-amber-500/30">
                  <Calendar className="h-3.5 w-3.5" />
                  {ev.original_expression || 'Normalized Date'}
                </span>

                <span className="text-[10px] font-mono uppercase tracking-wider text-[#9292A5] font-semibold bg-[#101019] px-2 py-0.5 rounded border border-[#232336]">
                  {ev.event_type || 'OCCURRENCE'}
                </span>
              </div>

              <h3 className="text-base font-bold text-[#F5F3FF] group-hover:text-amber-300 transition-colors">
                {ev.title}
              </h3>

              {/* Participants */}
              {ev.participants && ev.participants.length > 0 && (
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-[#1F1F2E] text-xs text-[#9292A5]">
                  <Users className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Participants: {ev.participants.join(', ')}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      )}

      {/* Selected Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-[#232336] bg-[#151521] p-6 shadow-2xl">
            <div className="flex items-start justify-between pb-4 border-b border-[#232336]">
              <div>
                <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-wider">
                  Timeline Event Anchor
                </span>
                <h3 className="text-lg font-bold text-[#F5F3FF] mt-1">{selectedEvent.title}</h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-[#9292A5] hover:text-[#F5F3FF] p-1 rounded-md"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-[#101019] border border-[#232336] space-y-1">
                <span className="text-[#9292A5]">Raw Mention in Text:</span>
                <p className="text-[#F5F3FF] font-medium font-sans">
                  "{selectedEvent.original_expression}"
                </p>
              </div>

              {selectedEvent.normalized_date && (
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#101019] border border-[#232336]">
                  <span className="text-[#9292A5]">Normalized ISO Timestamp:</span>
                  <span className="font-mono text-[#F5F3FF] font-bold">
                    {new Date(selectedEvent.normalized_date).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#232336]">
              <button
                onClick={() => {
                  const q = selectedEvent.title;
                  setSelectedEvent(null);
                  navigate(`/app/search?q=${encodeURIComponent(q)}`);
                }}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#6366F1] px-4 py-2.5 text-xs font-bold text-white shadow-md hover:opacity-95 transition-all"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Ask Echoes About This Event
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
