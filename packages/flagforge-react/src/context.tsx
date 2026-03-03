import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { FlagContextValue, FlagForgeConfig, Flags } from "./types";

// ─── Context ────────────────────────────────────────────────────────────────

const FlagContext = createContext<FlagContextValue>({
  flags: {},
  isLoading: true,
  error: null,
  isEnabled: () => false,
  refetch: () => {},
});

// ─── Provider ───────────────────────────────────────────────────────────────

export interface FlagProviderProps extends FlagForgeConfig {
  children: ReactNode;
  /** Pre-loaded flags (e.g. from SSR / Next.js server components) */
  initialFlags?: Flags;
}

/**
 * Wraps your app and provides feature flag values to all descendant components.
 *
 * @example
 * // main.tsx
 * <FlagProvider apiUrl="/api/flags/" headers={{ Authorization: `Bearer ${token}` }}>
 *   <App />
 * </FlagProvider>
 */
export function FlagProvider({
  children,
  apiUrl = "/api/flags/",
  headers,
  defaultValue = false,
  initialFlags = {},
}: FlagProviderProps) {
  const [flags, setFlags] = useState<Flags>(initialFlags);
  const [isLoading, setIsLoading] = useState(Object.keys(initialFlags).length === 0);
  const [error, setError] = useState<Error | null>(null);
  const [tick, setTick] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);

    fetch(apiUrl, {
      credentials: "include",
      headers: { Accept: "application/json", ...headers },
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`FlagForge: HTTP ${res.status} from ${apiUrl}`);
        return res.json() as Promise<Flags>;
      })
      .then((data) => {
        setFlags(data);
        setError(null);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err);
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });

    return () => controller.abort();
  }, [apiUrl, JSON.stringify(headers), tick]); // eslint-disable-line react-hooks/exhaustive-deps

  const isEnabled = useCallback(
    (key: string) => flags[key] ?? defaultValue,
    [flags, defaultValue]
  );

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return (
    <FlagContext.Provider value={{ flags, isLoading, error, isEnabled, refetch }}>
      {children}
    </FlagContext.Provider>
  );
}

// ─── Hooks ──────────────────────────────────────────────────────────────────

/**
 * Access the full FlagForge context (flags, loading state, refetch, etc.).
 * Must be used inside <FlagProvider>.
 */
export function useFlagForge(): FlagContextValue {
  return useContext(FlagContext);
}

/**
 * Check whether a single feature flag is enabled.
 * Returns `false` (or the provider's defaultValue) for unknown flags.
 *
 * @example
 * const showNewUI = useFlag("new_dashboard");
 */
export function useFlag(key: string, defaultValue?: boolean): boolean {
  const { flags, isEnabled } = useContext(FlagContext);
  if (key in flags) {
    return flags[key];
  }
  return defaultValue ?? isEnabled(key);
}

/**
 * Evaluate multiple flags at once.
 *
 * @example
 * const { new_dashboard, beta_checkout } = useFlags(["new_dashboard", "beta_checkout"]);
 */
export function useFlags<K extends string>(keys: K[]): Record<K, boolean> {
  const { flags, isEnabled } = useContext(FlagContext);
  // Re-evaluate only when flags change or keys list changes
  const result = {} as Record<K, boolean>;
  for (const key of keys) {
    result[key] = isEnabled(key);
  }
  return result;
}
