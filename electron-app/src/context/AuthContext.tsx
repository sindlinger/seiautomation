import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { STORAGE_KEYS } from '../config';
import { api, setAuthToken } from '../services/api';
import type { Token, User } from '../types/api';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const tokenFromStorage = (): string | null => {
  if (typeof localStorage === 'undefined') {
    return null;
  }
  return localStorage.getItem(STORAGE_KEYS.token);
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(tokenFromStorage);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const persistToken = useCallback((value: string | null) => {
    if (typeof localStorage === 'undefined') {
      return;
    }
    if (value) {
      localStorage.setItem(STORAGE_KEYS.token, value);
    } else {
      localStorage.removeItem(STORAGE_KEYS.token);
    }
  }, []);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const { data } = await api.get<User>('/auth/me');
      setUser(data);
    } catch (error) {
      console.error('Falha ao carregar usuário atual', error);
      setToken(null);
      setUser(null);
      setAuthToken(null);
      persistToken(null);
    }
  }, [persistToken]);

  useEffect(() => {
    setAuthToken(token);
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    fetchCurrentUser().finally(() => setLoading(false));
  }, [token, fetchCurrentUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const form = new URLSearchParams();
      form.append('username', email);
      form.append('password', password);

      const { data } = await api.post<Token>('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      setToken(data.access_token);
      persistToken(data.access_token);
      setAuthToken(data.access_token);
      await fetchCurrentUser();
    },
    [fetchCurrentUser, persistToken]
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setAuthToken(null);
    persistToken(null);
  }, [persistToken]);

  const value = useMemo<AuthContextValue>(
    () => ({ token, user, loading, login, logout }),
    [token, user, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};
