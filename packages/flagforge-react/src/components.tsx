import type { ReactNode } from "react";
import { useFlag } from "./context";

// ─── <Feature> ───────────────────────────────────────────────────────────────

export interface FeatureProps {
  /** Feature flag key to check */
  flag: string;
  /** Rendered when the flag is enabled */
  children: ReactNode;
  /** Rendered when the flag is disabled (optional) */
  fallback?: ReactNode;
}

/**
 * Declaratively render content based on a feature flag.
 *
 * @example
 * <Feature flag="new_dashboard">
 *   <NewDashboard />
 * </Feature>
 *
 * @example
 * <Feature flag="new_dashboard" fallback={<OldDashboard />}>
 *   <NewDashboard />
 * </Feature>
 */
export function Feature({ flag, children, fallback = null }: FeatureProps) {
  const enabled = useFlag(flag);
  return <>{enabled ? children : fallback}</>;
}
