/** Signed-in state. The token itself is held by `tokenStore`. */
import { create } from "zustand";

import { api, setApiToken, setUnauthorizedHandler } from "./api";
import { tokenStore } from "./token-store";
import type { Session, User } from "./types";

type AuthState = {
  ready: boolean;
  token: string | null;
  user: User | null;
  restore: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

export const useAuth = create<AuthState>((set, get) => {
  const open = async ({ token, user }: Session) => {
    setApiToken(token);
    await tokenStore.set(token);
    set({ token, user });
  };

  setUnauthorizedHandler(() => void get().logout());

  return {
    ready: false,
    token: null,
    user: null,

    restore: async () => {
      const token = await tokenStore.get();
      if (token) {
        setApiToken(token);
        try {
          const { user } = await api<{ user: User }>("/auth/me");
          set({ token, user });
        } catch {
          setApiToken(null);
          await tokenStore.clear();
        }
      }
      set({ ready: true });
    },

    login: async (email, password) =>
      open(await api<Session>("/auth/login", { body: { email, password } })),

    register: async (name, email, password) =>
      open(
        await api<Session>("/auth/register", {
          body: { name, email, password },
        }),
      ),

    logout: async () => {
      setApiToken(null);
      set({ token: null, user: null });
      await tokenStore.clear();
    },
  };
});
