import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, DEFAULT_WORKSPACE_ID } from '../services/api';
import {
  signInWithEmailPassword,
  signUpWithEmailPassword,
  formatFirebaseError,
} from '../services/firebase';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  workspaceId: string;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  loginGoogle: (params?: {
    credential?: string;
    email?: string;
    displayName?: string;
    avatarUrl?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('echoes_token'));
  const [workspaceId, setWorkspaceId] = useState<string>(
    () => localStorage.getItem('echoes_workspace_id') || DEFAULT_WORKSPACE_ID
  );
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize and validate session
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('echoes_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const profile = await api.getMe();
        setUser(profile.user);
        if (profile.workspace_id) {
          setWorkspaceId(profile.workspace_id);
          localStorage.setItem('echoes_workspace_id', profile.workspace_id);
        }
      } catch (err) {
        console.warn('Session expired or invalid, logging out', err);
        localStorage.removeItem('echoes_token');
        localStorage.removeItem('echoes_workspace_id');
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // 1. Authenticate with Firebase Email/Password
      const fbUser = await signInWithEmailPassword(email, password);

      // 2. Synchronize user and personal workspace in MongoDB Atlas
      const res = await api.loginWithGoogle({
        credential: fbUser.idToken,
        email: fbUser.email,
        displayName: fbUser.displayName,
        avatarUrl: fbUser.photoURL,
      });

      localStorage.setItem('echoes_token', res.access_token);
      localStorage.setItem('echoes_workspace_id', res.workspace_id);
      setToken(res.access_token);
      setUser(res.user);
      setWorkspaceId(res.workspace_id);
    } catch (err: any) {
      if (err.code) {
        throw new Error(formatFirebaseError(err));
      }
      // Fallback: try native backend login if not found in Firebase
      try {
        const res = await api.login(email, password);
        localStorage.setItem('echoes_token', res.access_token);
        localStorage.setItem('echoes_workspace_id', res.workspace_id);
        setToken(res.access_token);
        setUser(res.user);
        setWorkspaceId(res.workspace_id);
      } catch {
        const msg = err.response?.data?.detail || err.message || 'Login failed.';
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, displayName: string) => {
    setIsLoading(true);
    try {
      // 1. Create account with Firebase Email/Password
      const fbUser = await signUpWithEmailPassword(email, password, displayName);

      // 2. Provision user vault and personal workspace in MongoDB Atlas
      const res = await api.loginWithGoogle({
        credential: fbUser.idToken,
        email: fbUser.email,
        displayName: fbUser.displayName,
        avatarUrl: fbUser.photoURL,
      });

      localStorage.setItem('echoes_token', res.access_token);
      localStorage.setItem('echoes_workspace_id', res.workspace_id);
      setToken(res.access_token);
      setUser(res.user);
      setWorkspaceId(res.workspace_id);
    } catch (err: any) {
      if (err.code) {
        throw new Error(formatFirebaseError(err));
      }
      const msg = err.response?.data?.detail || err.message || 'Registration failed.';
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  const loginGoogle = async (
    params: {
      credential?: string;
      email?: string;
      displayName?: string;
      avatarUrl?: string;
    } = {}
  ) => {
    setIsLoading(true);
    try {
      const res = await api.loginWithGoogle(params);
      localStorage.setItem('echoes_token', res.access_token);
      localStorage.setItem('echoes_workspace_id', res.workspace_id);
      setToken(res.access_token);
      setUser(res.user);
      setWorkspaceId(res.workspace_id);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      localStorage.removeItem('echoes_token');
      localStorage.removeItem('echoes_workspace_id');
      setToken(null);
      setUser(null);
      setWorkspaceId(DEFAULT_WORKSPACE_ID);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        workspaceId,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        loginGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
