# flagforge-react

**React hooks and components for [FlagForge](https://github.com/nayanjaiswalgit/flagforge) feature flags**

[![npm version](https://badge.fury.io/js/flagforge-react.svg)](https://badge.fury.io/js/flagforge-react)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Consumes the FlagForge REST API (`GET /api/flags/`) and exposes the resolved flags to your React app via context, hooks, and the `<Feature>` component. Also includes first-class **TanStack Query (React Query v5)** support.

---

## Installation

```bash
# npm
npm install flagforge-react

# pnpm
pnpm add flagforge-react

# yarn
yarn add flagforge-react
```

### With React Query support

```bash
npm install flagforge-react @tanstack/react-query
```

---

## Requirements

- React 17+
- Your backend running FlagForge (Django or FastAPI) with the flags REST API mounted

---

## Quick Start

### 1. Wrap your app

```tsx
// main.tsx
import { FlagProvider } from "flagforge-react";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <FlagProvider apiUrl="/api/flags/">
    <App />
  </FlagProvider>
);
```

With authentication:

```tsx
<FlagProvider
  apiUrl="/api/flags/"
  headers={{ Authorization: `Bearer ${token}` }}
>
  <App />
</FlagProvider>
```

### 2. Use hooks

```tsx
import { useFlag, useFlags } from "flagforge-react";

// Single flag
function Navbar() {
  const showBeta = useFlag("beta_feature");
  return <nav>{showBeta && <BetaBadge />}</nav>;
}

// Multiple flags at once
function App() {
  const { new_dashboard, dark_mode } = useFlags(["new_dashboard", "dark_mode"]);
  return <div className={dark_mode ? "dark" : "light"}>...</div>;
}
```

### 3. Use the `<Feature>` component

```tsx
import { Feature } from "flagforge-react";

function Dashboard() {
  return (
    <Feature flag="new_dashboard" fallback={<LegacyDashboard />}>
      <NewDashboard />
    </Feature>
  );
}
```

---

## API

### `<FlagProvider>`

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiUrl` | `string` | `"/api/flags/"` | FlagForge API endpoint |
| `headers` | `Record<string, string>` | `{}` | Extra request headers (e.g. `Authorization`) |
| `defaultValue` | `boolean` | `false` | Value returned for unknown flags |
| `initialFlags` | `Record<string, boolean>` | `{}` | Pre-loaded flags (SSR) |
| `children` | `ReactNode` | — | Your app |

### `useFlag(key: string): boolean`

Returns `true` if the flag is enabled, `false` otherwise.

### `useFlags(keys: string[]): Record<string, boolean>`

Returns an object mapping each key to its enabled state.

### `useFlagForge(): FlagContextValue`

Returns `{ flags, isLoading, error, isEnabled, refetch }`.

### `<Feature flag="..." fallback={...}>`

Renders `children` when flag is on, `fallback` (or `null`) when off.

---

## React Query Integration

If you already use TanStack Query, use the query hooks instead of the context provider. These plug into your existing `QueryClient` for unified cache management.

```tsx
// main.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);
```

```tsx
// Anywhere in your app
import { useFlagForgeQuery, useFlagQuery, useFlagsQuery } from "flagforge-react";

// All flags — full React Query result (data, isLoading, error, refetch…)
function App() {
  const { data: flags = {}, isLoading } = useFlagForgeQuery({
    apiUrl: "/api/flags/",
    staleTime: 5 * 60 * 1000,   // 5 minutes
  });

  if (isLoading) return <Spinner />;
  return flags.new_dashboard ? <NewDashboard /> : <OldDashboard />;
}

// Single flag — returns boolean directly
function Navbar() {
  const showBeta = useFlagQuery("beta_feature");
  return <nav>{showBeta && <BetaBadge />}</nav>;
}

// Multiple flags
function Settings() {
  const { dark_mode, ai_suggestions } = useFlagsQuery(["dark_mode", "ai_suggestions"]);
  return <SettingsPanel darkMode={dark_mode} aiEnabled={ai_suggestions} />;
}
```

### Invalidate flags cache after login

```tsx
import { useQueryClient } from "@tanstack/react-query";
import { flagforgeKeys } from "flagforge-react";

function LoginButton() {
  const queryClient = useQueryClient();

  const handleLogin = async () => {
    await loginUser();
    // Re-fetch flags now that user is authenticated
    await queryClient.invalidateQueries({ queryKey: flagforgeKeys.all });
  };

  return <button onClick={handleLogin}>Log in</button>;
}
```

---

## Next.js Integration

### App Router (server-side pre-fetch)

```tsx
// app/layout.tsx
import { FlagProvider } from "flagforge-react";

async function getFlags(token?: string) {
  const res = await fetch(`${process.env.API_URL}/api/flags/`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: "no-store",
  });
  if (!res.ok) return {};
  return res.json();
}

export default async function RootLayout({ children }) {
  const flags = await getFlags();  // runs on the server

  return (
    <html>
      <body>
        <FlagProvider initialFlags={flags} apiUrl="/api/flags/">
          {children}
        </FlagProvider>
      </body>
    </html>
  );
}
```

### Pages Router

```tsx
// pages/_app.tsx
import type { AppProps } from "next/app";
import { FlagProvider } from "flagforge-react";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <FlagProvider apiUrl="/api/flags/">
      <Component {...pageProps} />
    </FlagProvider>
  );
}
```

---

## TypeScript: Typed Flag Keys

```ts
// flags.ts
export type FlagKey =
  | "new_dashboard"
  | "beta_checkout"
  | "dark_mode"
  | "ai_suggestions";
```

```tsx
import { useFlag } from "flagforge-react";
import type { FlagKey } from "./flags";

// Wrap useFlag with your typed key union
function useTypedFlag(key: FlagKey): boolean {
  return useFlag(key);
}
```

---

## Full Example

```tsx
import { FlagProvider, Feature, useFlag, useFlags } from "flagforge-react";

// main.tsx
ReactDOM.createRoot(document.getElementById("root")!).render(
  <FlagProvider apiUrl="/api/flags/" headers={{ Authorization: `Bearer ${token}` }}>
    <App />
  </FlagProvider>
);

// App.tsx
function App() {
  const darkMode = useFlag("dark_mode");
  const { new_dashboard, beta_checkout } = useFlags(["new_dashboard", "beta_checkout"]);

  return (
    <div className={darkMode ? "dark" : "light"}>
      {/* Declarative rendering */}
      <Feature flag="new_dashboard" fallback={<LegacyDashboard />}>
        <NewDashboard />
      </Feature>

      {/* Inline conditional */}
      {beta_checkout && <BetaCheckoutBanner />}
    </div>
  );
}
```

---

## License

MIT — [Nayan Jaiswal](mailto:jaiswal2062@gmail.com)
