/**
 * React Query (TanStack Query v5) integration for FlagForge.
 *
 * Install peer dep:  npm install @tanstack/react-query
 *
 * Usage:
 *   import { useFlagQuery, useFlagForgeQuery } from "flagforge-react/query"
 */

import { useQuery, type UseQueryOptions, type UseQueryResult } from "@tanstack/react-query";
import type { Flags } from "./types";

// ─── Query key factory ───────────────────────────────────────────────────────

export const flagforgeKeys = {
  all: ["flagforge"] as const,
  flags: (apiUrl: string) => ["flagforge", "flags", apiUrl] as const,
};

// ─── Fetch helper ────────────────────────────────────────────────────────────

async function fetchFlags(
  apiUrl: string,
  headers?: Record<string, string>
): Promise<Flags> {
  const res = await fetch(apiUrl, {
    credentials: "include",
    headers: { Accept: "application/json", ...headers },
  });
  if (!res.ok) throw new Error(`FlagForge: HTTP ${res.status} from ${apiUrl}`);
  return res.json();
}

// ─── useFlagForgeQuery ───────────────────────────────────────────────────────

export interface UseFlagForgeQueryOptions
  extends Omit<UseQueryOptions<Flags, Error>, "queryKey" | "queryFn"> {
  apiUrl?: string;
  headers?: Record<string, string>;
}

/**
 * Fetch all feature flags via React Query (TanStack Query v5).
 * Handles caching, background refetching, and stale-while-revalidate automatically.
 *
 * @example
 * const { data: flags = {}, isLoading } = useFlagForgeQuery({
 *   apiUrl: "/api/flags/",
 *   staleTime: 5 * 60 * 1000,
 * });
 */
export function useFlagForgeQuery({
  apiUrl = "/api/flags/",
  headers,
  staleTime = 5 * 60 * 1000, // 5 minutes default
  ...options
}: UseFlagForgeQueryOptions = {}): UseQueryResult<Flags, Error> {
  return useQuery<Flags, Error>({
    queryKey: flagforgeKeys.flags(apiUrl),
    queryFn: () => fetchFlags(apiUrl, headers),
    staleTime,
    ...options,
  });
}

// ─── useFlagQuery ─────────────────────────────────────────────────────────────

/**
 * Check a single feature flag using React Query.
 * Returns the flag value directly (no loading/error handling needed for simple cases).
 *
 * @example
 * const newDashboard = useFlagQuery("new_dashboard");
 * if (newDashboard) return <NewDashboard />;
 */
export function useFlagQuery(
  key: string,
  options?: UseFlagForgeQueryOptions
): boolean {
  const { data: flags = {} } = useFlagForgeQuery(options);
  return flags[key] ?? false;
}

// ─── useFlagsQuery ────────────────────────────────────────────────────────────

/**
 * Evaluate multiple flags using React Query.
 *
 * @example
 * const { new_dashboard, beta_checkout } = useFlagsQuery(["new_dashboard", "beta_checkout"]);
 */
export function useFlagsQuery<K extends string>(
  keys: K[],
  options?: UseFlagForgeQueryOptions
): Record<K, boolean> {
  const { data: flags = {} } = useFlagForgeQuery(options);
  const result = {} as Record<K, boolean>;
  for (const key of keys) {
    result[key] = flags[key] ?? false;
  }
  return result;
}
