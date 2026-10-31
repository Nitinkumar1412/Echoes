import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { User, Briefcase, Cpu, Calendar, Compass, Lightbulb, CheckCircle } from 'lucide-react';
import type { EntityType } from '../types';

interface MemoryNodeProps {
  data: {
    label: string;
    type: EntityType;
    mentions: number;
    selected?: boolean;
  };
}

const typeStyles: Record<
  string,
  { bg: string; border: string; glow: string; text: string; icon: React.FC<{ className?: string }> }
> = {
  PERSON: {
    bg: 'bg-emerald-950/60',
    border: 'border-emerald-500/50',
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.25)]',
    text: 'text-emerald-300',
    icon: User,
  },
  PROJECT: {
    bg: 'bg-violet-950/60',
    border: 'border-violet-500/50',
    glow: 'shadow-[0_0_20px_rgba(139,92,246,0.3)]',
    text: 'text-violet-300',
    icon: Briefcase,
  },
  TECHNOLOGY: {
    bg: 'bg-indigo-950/60',
    border: 'border-indigo-500/50',
    glow: 'shadow-[0_0_20px_rgba(99,102,241,0.25)]',
    text: 'text-indigo-300',
    icon: Cpu,
  },
  DECISION: {
    bg: 'bg-amber-950/60',
    border: 'border-amber-500/50',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.25)]',
    text: 'text-amber-300',
    icon: CheckCircle,
  },
  CONCEPT: {
    bg: 'bg-cyan-950/60',
    border: 'border-cyan-500/50',
    glow: 'shadow-[0_0_20px_rgba(6,182,212,0.25)]',
    text: 'text-cyan-300',
    icon: Lightbulb,
  },
  OTHER: {
    bg: 'bg-slate-900/60',
    border: 'border-slate-500/40',
    glow: 'shadow-[0_0_15px_rgba(100,116,139,0.2)]',
    text: 'text-slate-300',
    icon: Compass,
  },
};

export const MemoryNode: React.FC<MemoryNodeProps> = memo(({ data }) => {
  const style = typeStyles[data.type] || typeStyles.OTHER;
  const Icon = style.icon;

  return (
    <div
      className={`group relative rounded-xl border px-3.5 py-2.5 transition-all duration-300 backdrop-blur-md cursor-pointer ${
        style.bg
      } ${style.border} ${style.glow} hover:scale-105 active:scale-95 ${
        data.selected ? 'ring-2 ring-white shadow-lg' : ''
      }`}
      style={{ minWidth: 150 }}
    >
      <Handle type="target" position={Position.Top} className="!bg-[#A78BFA] !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-[#A78BFA] !w-2 !h-2" />

      <div className="flex items-center gap-2.5">
        <div className={`p-1.5 rounded-lg bg-black/40 ${style.text}`}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-xs font-semibold text-[#F5F3FF] truncate">{data.label}</span>
          <div className="flex items-center gap-1.5">
            <span className={`text-[9px] uppercase tracking-wider font-bold ${style.text}`}>
              {data.type}
            </span>
            <span className="text-[9px] text-[#9292A5]">· {data.mentions} ref</span>
          </div>
        </div>
      </div>
    </div>
  );
});
