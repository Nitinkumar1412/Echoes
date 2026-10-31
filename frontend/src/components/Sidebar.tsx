import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Search,
  LayoutDashboard,
  Network,
  Clock,
  BookOpen,
  FolderGit2,
  Settings,
  ChevronLeft,
  ChevronRight,
  Database,
  User,
  Plus,
  LogOut,
} from 'lucide-react';
import { echoesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    echoesApi.checkHealth().then((res) => {
      setDbStatus(res.database === 'connected' ? 'connected' : 'disconnected');
    });
  }, []);

  const navItems = [
    { label: 'Overview', to: '/app', icon: LayoutDashboard, end: true },
    { label: 'AI Search', to: '/app/search', icon: Search },
    { label: 'Memory Graph', to: '/app/graph', icon: Network },
    { label: 'Timeline', to: '/app/timeline', icon: Clock },
    { label: 'Memory Library', to: '/app/library', icon: BookOpen },
    { label: 'Sources & Uploads', to: '/app/sources', icon: FolderGit2 },
    { label: 'Settings', to: '/app/settings', icon: Settings },
  ];

  return (
    <aside
      className={`relative flex flex-col border-r border-[#232336] bg-[#101019] transition-all duration-300 ease-in-out z-30 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-[#232336]">
        <div
          onClick={() => navigate('/app')}
          className="flex items-center gap-3 cursor-pointer group overflow-hidden"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-[#8B5CF6] to-[#6366F1] shadow-md shadow-[#8B5CF6]/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-[#F5F3FF] text-base">
                Echoes<span className="text-[#8B5CF6]">.</span>
              </span>
              <span className="text-[10px] tracking-wider text-[#9292A5] uppercase font-semibold">
                Memory RAG
              </span>
            </div>
          )}
        </div>

        {/* Toggle Collapse */}
        <button
          onClick={onToggle}
          className="hidden md:flex h-7 w-7 items-center justify-center rounded-lg border border-[#232336] bg-[#151521] text-[#9292A5] hover:text-[#F5F3FF] hover:border-[#3D3D5C] transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Quick Action Button */}
      <div className="p-3">
        <button
          onClick={() => navigate('/app/search')}
          className={`flex w-full items-center justify-center gap-2 rounded-xl bg-[#8B5CF6] py-2.5 font-medium text-white shadow-lg shadow-[#8B5CF6]/20 hover:bg-[#7C3AED] transition-all active:scale-[0.98] ${
            collapsed ? 'px-0' : 'px-4'
          }`}
          title="New Search"
        >
          <Plus className="h-4 w-4 shrink-0" />
          {!collapsed && <span className="text-sm font-semibold">New Search</span>}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-3 py-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-[#1E1E30] text-[#F5F3FF] shadow-sm shadow-black/20 border border-[#8B5CF6]/40'
                  : 'text-[#9292A5] hover:bg-[#151521] hover:text-[#F5F3FF]'
              } ${collapsed ? 'justify-center px-0' : ''}`
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Status & Profile */}
      <div className="border-t border-[#232336] p-3 space-y-2">
        {/* Live DB Status Pill */}
        <div
          className={`flex items-center gap-2 rounded-lg bg-[#151521] px-2.5 py-1.5 text-xs ${
            collapsed ? 'justify-center' : 'justify-between'
          }`}
        >
          <div className="flex items-center gap-2 overflow-hidden">
            <span
              className={`h-2 w-2 rounded-full shrink-0 ${
                dbStatus === 'connected'
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]'
                  : dbStatus === 'checking'
                  ? 'bg-amber-400'
                  : 'bg-rose-400'
              }`}
            />
            {!collapsed && (
              <span className="text-[11px] text-[#9292A5] truncate">
                {dbStatus === 'connected' ? 'Atlas Connected' : 'Atlas Offline'}
              </span>
            )}
          </div>
          {!collapsed && <Database className="h-3.5 w-3.5 text-[#64647A] shrink-0" />}
        </div>

        {/* User Card */}
        <div
          className={`flex items-center gap-2.5 rounded-xl bg-[#151521] p-2 hover:bg-[#1A1A2B] transition-colors ${
            collapsed ? 'justify-center' : 'justify-between'
          }`}
        >
          <div
            onClick={() => navigate('/app/settings')}
            className="flex items-center gap-2.5 min-w-0 cursor-pointer flex-1"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-[#6366F1] to-[#8B5CF6] text-white font-bold text-xs uppercase shadow-sm">
              {user?.display_name
                ? user.display_name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .slice(0, 2)
                : 'EC'}
            </div>
            {!collapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-[#F5F3FF] truncate">
                  {user?.display_name || 'Personal Memory'}
                </span>
                <span className="text-[10px] text-[#9292A5] truncate">
                  {user?.email || 'Active Vault'}
                </span>
              </div>
            )}
          </div>

          {!collapsed && (
            <button
              onClick={async (e) => {
                e.stopPropagation();
                await logout();
                navigate('/login');
              }}
              title="Sign Out"
              className="p-1.5 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};
