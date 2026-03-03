export type Flags = Record<string, boolean>;

export interface FlagForgeConfig {
  /** URL of the FlagForge flags endpoint. Default: "/api/flags/" */
  apiUrl?: string;
  /** Extra headers (e.g. Authorization) passed on every request */
  headers?: Record<string, string>;
  /** Stale time in ms for React Query. Default: 5 minutes */
  staleTime?: number;
  /** Default value returned for unknown flags. Default: false */
  defaultValue?: boolean;
}

export interface FlagContextValue {
  flags: Flags;
  isLoading: boolean;
  error: Error | null;
  /** Check if a flag is enabled (returns defaultValue if unknown) */
  isEnabled: (key: string) => boolean;
  /** Force re-fetch of all flags (e.g. after login) */
  refetch: () => void;
}
