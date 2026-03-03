// Context-based API (built-in fetch, no extra deps)
export { FlagProvider, useFlagForge, useFlag, useFlags } from "./context";
export type { FlagProviderProps } from "./context";

// Components
export { Feature } from "./components";
export type { FeatureProps } from "./components";

// Types
export type { Flags, FlagForgeConfig, FlagContextValue } from "./types";

// React Query integration (requires @tanstack/react-query)
// Import separately: import { useFlagForgeQuery } from "flagforge-react/query"
export {
  useFlagForgeQuery,
  useFlagQuery,
  useFlagsQuery,
  flagforgeKeys,
} from "./query";
export type { UseFlagForgeQueryOptions } from "./query";
