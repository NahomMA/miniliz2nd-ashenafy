/** Signed-in state. The token lives only in the device's encrypted store. */
import * as SecureStore from 'expo-secure-store';
import { create } from 'zustand';

import { api, setApiToken, setUnauthorizedHandler } from './api';
import type { Session, User } from './types';

const TOKEN_KEY = 'access_token';

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
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    set({ token, user });
  };

  setUnauthorizedHandler(() => void get().logout());

  return {
    ready: false,
    token: null,
    user: null,

    restore: async () => {
      const token = await SecureStore.getItemAsync(TOKEN_KEY).catch(() => null);
      if (token) {
        setApiToken(token);
        try {
          const { user } = await api<{ user: User }>('/auth/me');
          set({ token, user });
        } catch {
          setApiToken(null);
          await SecureStore.deleteItemAsync(TOKEN_KEY).catch(() => {});
        }
      }
      set({ ready: true });
    },

    login: async (email, password) => open(await api<Session>('/auth/login', { body: { email, password } })),

    register: async (name, email, password) =>
      open(await api<Session>('/auth/register', { body: { name, email, password } })),

    logout: async () => {
      setApiToken(null);
      set({ token: null, user: null });
      await SecureStore.deleteItemAsync(TOKEN_KEY).catch(() => {});
    },
  };
});
