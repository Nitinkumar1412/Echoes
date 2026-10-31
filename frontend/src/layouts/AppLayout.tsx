import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen w-full bg-[#09090F] text-[#F5F3FF] overflow-hidden selection:bg-[#8B5CF6]/40">
      {/* Collapsible Left Sidebar */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* Main App Content Area */}
      <main className="flex-1 overflow-y-auto bg-[#09090F] relative">
        <Outlet />
      </main>
    </div>
  );
};
