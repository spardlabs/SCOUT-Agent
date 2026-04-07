"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { UserResponse } from "@/types/api";
import { usersApi } from "@/lib/api/users";

interface AuthContextType {
  apiKey: string | null;
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (apiKey: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  apiKey: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  useEffect(() => {
    const stored = localStorage.getItem("scout_api_key");
    if (stored) {
      setApiKey(stored);
      usersApi
        .me()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem("scout_api_key");
          setApiKey(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback((key: string) => {
    localStorage.setItem("scout_api_key", key);
    setApiKey(key);
    setIsLoading(true);
    usersApi
      .me()
      .then(setUser)
      .finally(() => setIsLoading(false));
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("scout_api_key");
    setApiKey(null);
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  return (
    <AuthContext.Provider
      value={{
        apiKey,
        user,
        isAuthenticated: !!apiKey && !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
