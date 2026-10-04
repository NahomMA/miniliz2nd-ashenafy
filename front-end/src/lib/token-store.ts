/**
 * Where the access token is kept.
 * On a phone: the device's encrypted store (Keychain / Keystore) through expo-secure-store.
 * In a browser, where that store does not exist: sessionStorage, which is cleared when the tab closes.
 */
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const KEY = "access_token";
const onWeb = Platform.OS === "web";

export const tokenStore = {
  async get(): Promise<string | null> {
    try {
      return onWeb
        ? globalThis.sessionStorage.getItem(KEY)
        : await SecureStore.getItemAsync(KEY);
    } catch {
      return null;
    }
  },

  async set(token: string): Promise<void> {
    if (onWeb) globalThis.sessionStorage.setItem(KEY, token);
    else await SecureStore.setItemAsync(KEY, token);
  },

  async clear(): Promise<void> {
    try {
      if (onWeb) globalThis.sessionStorage.removeItem(KEY);
      else await SecureStore.deleteItemAsync(KEY);
    } catch {
      // Nothing stored, or storage unavailable: there is nothing to clear.
    }
  },
};
