import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles } from 'lucide-react';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#09090F] flex flex-col items-center justify-center relative overflow-hidden">
        {/* Ambient Glow */}
        <div className="absolute w-96 h-96 rounded-full bg-violet-600/15 blur-[120px] pointer-events-none" />
        
        <div className="relative z-10 flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 p-0.5 animate-pulse shadow-lg shadow-violet-500/20">
            <div className="w-full h-full bg-[#101019] rounded-2xl flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-violet-400 animate-spin" style={{ animationDuration: '3s' }} />
            </div>
          </div>
          <div className="text-center">
            <h3 className="text-sm font-semibold text-zinc-200">Reconstructing Session</h3>
            <p className="text-xs text-zinc-500 mt-1">Connecting to your personal memory vault...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : null;
};
