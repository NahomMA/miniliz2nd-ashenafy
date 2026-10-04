/** The only module that talks to the backend. Adds the bearer token and normalizes errors. */
import Constants from 'expo-constants';

/**
 * Backend address: an explicit setting wins (EXPO_PUBLIC_API_URL, then `extra.apiUrl` in app.json).
 * In development with neither set, requests go to `/api` on the Expo dev server, which forwards them to the
 * local backend (see metro.config.js). Any phone that can load the app can therefore reach the API.
 */
function resolveBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_URL || Constants.expoConfig?.extra?.apiUrl;
  if (configured) return String(configured).replace(/\/$/, '');
  return `http://${Constants.expoConfig?.hostUri ?? 'localhost:8081'}/api`;
}

const BASE_URL = resolveBaseUrl();
const TIMEOUT_MS = 30_000;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly field?: string,
  ) {
    super(message);
  }
}

let token: string | null = null;
let onUnauthorized: () => void = () => {};

export function setApiToken(value: string | null): void {
  token = value;
}

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

export async function api<T>(path: string, options: { method?: 'GET' | 'POST'; body?: unknown } = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(BASE_URL + path, {
      method: options.method ?? (options.body === undefined ? 'GET' : 'POST'),
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
  } catch {
    throw new ApiError("We can't reach the server right now. Check your connection and try again.", 0, 'network');
  } finally {
    clearTimeout(timer);
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized();
    const error = data?.error ?? {};
    throw new ApiError(error.message ?? 'Something went wrong. Please try again.', response.status, error.code ?? 'error', error.field);
  }
  return data as T;
}

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.';
}
