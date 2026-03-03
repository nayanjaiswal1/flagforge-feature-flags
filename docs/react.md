# React / Frontend Integration Guide

FlagForge exposes a REST endpoint (`GET /api/flags/`) that returns all resolved feature flag values for the current authenticated user. Your React (or any JS/TS) frontend fetches these once per page load and uses them throughout the component tree.

---

## How It Works

```
┌─────────────────┐        GET /api/flags/        ┌──────────────────┐
│   React App     │ ─────── Bearer <token> ──────▶ │  Django/FastAPI  │
│                 │ ◀──── { "new_dashboard": true } │  FlagForge API   │
└─────────────────┘                                └──────────────────┘
```

The response is a flat object of `{ flagKey: boolean }` values resolved for the current user and tenant. Your frontend renders different UI based on these values — no flag logic lives in the frontend.

---

## API Response Shape

```json
GET /api/flags/
Authorization: Bearer <token>

{
    "new_dashboard": true,
    "beta_checkout": false,
    "dark_mode": true,
    "ai_suggestions": false
}
```

---

## Setup

### Install nothing — just `fetch`

No npm package needed. FlagForge is a backend library. The frontend only needs to call the REST API.

---

## Core Hook: `useFlags`

```tsx
// src/hooks/useFlags.ts
import { useState, useEffect } from "react";

type Flags = Record<string, boolean>;

interface UseFlagsResult {
  flags: Flags;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useFlags(
  apiUrl: string = "/api/flags/",
  options?: RequestInit
): UseFlagsResult {
  const [flags, setFlags] = useState<Flags>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    fetch(apiUrl, {
      credentials: "include",
      ...options,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to fetch flags: ${res.status}`);
        return res.json() as Promise<Flags>;
      })
      .then((data) => {
        if (!cancelled) {
          setFlags(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [apiUrl, tick]);

  return { flags, loading, error, refetch: () => setTick((t) => t + 1) };
}
```

---

## Context Provider: `FlagProvider`

Wrap your app once with a provider so any component can access flags without prop drilling.

```tsx
// src/context/FlagContext.tsx
import React, { createContext, useContext, ReactNode } from "react";
import { useFlags } from "../hooks/useFlags";

type Flags = Record<string, boolean>;

interface FlagContextValue {
  flags: Flags;
  loading: boolean;
  isEnabled: (key: string) => boolean;
  refetch: () => void;
}

const FlagContext = createContext<FlagContextValue>({
  flags: {},
  loading: true,
  isEnabled: () => false,
  refetch: () => {},
});

interface FlagProviderProps {
  children: ReactNode;
  apiUrl?: string;
}

export function FlagProvider({
  children,
  apiUrl = "/api/flags/",
}: FlagProviderProps) {
  const { flags, loading, refetch } = useFlags(apiUrl);

  const isEnabled = (key: string): boolean => flags[key] ?? false;

  return (
    <FlagContext.Provider value={{ flags, loading, isEnabled, refetch }}>
      {children}
    </FlagContext.Provider>
  );
}

export function useFeatureFlags(): FlagContextValue {
  return useContext(FlagContext);
}

export function useFlag(key: string): boolean {
  const { isEnabled } = useContext(FlagContext);
  return isEnabled(key);
}
```

**Wrap your app:**

```tsx
// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { FlagProvider } from "./context/FlagContext";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <FlagProvider apiUrl="/api/flags/">
      <App />
    </FlagProvider>
  </React.StrictMode>
);
```

---

## `<Feature>` Component

A declarative component to conditionally render UI based on a flag:

```tsx
// src/components/Feature.tsx
import { ReactNode } from "react";
import { useFlag } from "../context/FlagContext";

interface FeatureProps {
  flag: string;
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Renders `children` when the feature flag is enabled.
 * Renders `fallback` (or nothing) when disabled.
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
```

---

## Usage Examples

### Basic on/off rendering

```tsx
import { Feature } from "./components/Feature";

function Dashboard() {
  return (
    <main>
      <Feature flag="new_dashboard" fallback={<LegacyDashboard />}>
        <NewDashboard />
      </Feature>
    </main>
  );
}
```

### Inline with `useFlag`

```tsx
import { useFlag } from "./context/FlagContext";

function Navbar() {
  const showBetaBadge = useFlag("beta_program");

  return (
    <nav>
      <a href="/">Home</a>
      {showBetaBadge && <span className="badge">BETA</span>}
    </nav>
  );
}
```

### Access all flags at once

```tsx
import { useFeatureFlags } from "./context/FlagContext";

function AppConfigDebug() {
  const { flags, loading } = useFeatureFlags();

  if (loading) return <p>Loading flags...</p>;

  return (
    <ul>
      {Object.entries(flags).map(([key, enabled]) => (
        <li key={key}>
          {key}: <strong>{enabled ? "ON" : "OFF"}</strong>
        </li>
      ))}
    </ul>
  );
}
```

### Route guard with React Router

```tsx
import { Navigate, Outlet } from "react-router-dom";
import { useFlag } from "./context/FlagContext";

function FlagGuard({ flag }: { flag: string }) {
  const enabled = useFlag(flag);
  return enabled ? <Outlet /> : <Navigate to="/" replace />;
}

// In your router:
<Route element={<FlagGuard flag="beta_feature" />}>
  <Route path="/beta" element={<BetaPage />} />
</Route>
```

### Loading state handling

```tsx
import { useFeatureFlags } from "./context/FlagContext";

function App() {
  const { loading } = useFeatureFlags();

  // Don't flash the wrong variant while flags load
  if (loading) {
    return <FullPageSpinner />;
  }

  return <RouterOutlet />;
}
```

### Refresh flags (e.g. after login)

```tsx
import { useFeatureFlags } from "./context/FlagContext";

function LoginButton() {
  const { refetch } = useFeatureFlags();

  const handleLogin = async () => {
    await loginUser();
    refetch(); // Re-fetch flags now that user is authenticated
  };

  return <button onClick={handleLogin}>Log in</button>;
}
```

---

## TypeScript: Typed Flag Keys

For autocompletion and safety, define your flag keys as a union type:

```tsx
// src/flags.ts
export type FlagKey =
  | "new_dashboard"
  | "beta_checkout"
  | "dark_mode"
  | "ai_suggestions";

// Typed wrapper
import { useContext } from "react";
import { FlagContext } from "./context/FlagContext";

export function useTypedFlag(key: FlagKey): boolean {
  const { flags } = useContext(FlagContext);
  return flags[key] ?? false;
}
```

```tsx
// Usage
const showDarkMode = useTypedFlag("dark_mode"); // autocompletes!
```

---

## Next.js Integration

### App Router (Server Components)

Fetch flags server-side and pass them down:

```tsx
// app/layout.tsx
import { cookies, headers } from "next/headers";
import { FlagProvider } from "@/context/FlagContext";

async function getFlags(): Promise<Record<string, boolean>> {
  const token = cookies().get("auth_token")?.value;
  const res = await fetch(`${process.env.API_URL}/api/flags/`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) return {};
  return res.json();
}

export default async function RootLayout({ children }) {
  const flags = await getFlags();

  return (
    <html>
      <body>
        {/* Pass server-fetched flags as initial value */}
        <FlagProvider initialFlags={flags}>
          {children}
        </FlagProvider>
      </body>
    </html>
  );
}
```

Update `FlagProvider` to accept `initialFlags`:

```tsx
interface FlagProviderProps {
  children: ReactNode;
  apiUrl?: string;
  initialFlags?: Record<string, boolean>;
}

export function FlagProvider({ children, apiUrl = "/api/flags/", initialFlags = {} }: FlagProviderProps) {
  const [flags, setFlags] = useState<Flags>(initialFlags);
  // ...
}
```

### Pages Router

```tsx
// pages/_app.tsx
import type { AppProps } from "next/app";
import { FlagProvider } from "@/context/FlagContext";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <FlagProvider apiUrl="/api/flags/">
      <Component {...pageProps} />
    </FlagProvider>
  );
}
```

---

## Complete Example App

```
src/
├── context/
│   └── FlagContext.tsx      # Provider + useFlag + useFeatureFlags
├── components/
│   └── Feature.tsx          # <Feature flag="..." fallback={...}>
├── hooks/
│   └── useFlags.ts          # Low-level fetch hook
├── flags.ts                 # Typed flag key union
├── App.tsx
└── main.tsx
```

**`App.tsx`:**

```tsx
import { Feature } from "./components/Feature";
import { useFlag, useFeatureFlags } from "./context/FlagContext";

function App() {
  const { loading } = useFeatureFlags();
  const darkMode = useFlag("dark_mode");

  if (loading) return <div>Loading...</div>;

  return (
    <div className={darkMode ? "theme-dark" : "theme-light"}>
      <Feature flag="new_dashboard" fallback={<LegacyDashboard />}>
        <NewDashboard />
      </Feature>

      <Feature flag="beta_checkout">
        <BetaCheckoutBanner />
      </Feature>
    </div>
  );
}
```

---

## Security Notes

- The `/api/flags/` endpoint only returns flags marked `is_public=True` for unauthenticated requests
- Authenticated users see all flags resolved for their tenant/user
- **Never gate security-sensitive logic purely on frontend flags** — always verify permissions on the backend
- Feature flags are for UI/UX control, not access control
