"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api, { clearAuth, getStoredUser, storeAuth } from "./api";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  user: null, loading: true,
  login: async () => {}, register: async () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const u = getStoredUser();
    if (u) setUser(u);
    setLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.post("/auth/login", { username, password });
    const { access_token, refresh_token } = res.data;
    storeAuth(access_token, refresh_token, { username });
    // fetch user
    const me = await api.get("/users/me");
    setUser(me.data);
    storeAuth(access_token, refresh_token, me.data);
  }, []);

  const register = useCallback(async (username: string, password: string, email: string) => {
    await api.post("/auth/register", { username, password, email });
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() { return useContext(AuthContext); }
