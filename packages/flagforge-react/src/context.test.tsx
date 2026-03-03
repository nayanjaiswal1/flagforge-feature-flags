import { renderHook } from "@testing-library/react";
import React from "react";
import { describe, it, expect } from "vitest";
import { FlagProvider, useFlag } from "./context";

describe("FlagProvider & useFlag", () => {
  it("provides flags and allows checking them", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <FlagProvider initialFlags={{ feature_a: true, feature_b: false }}>
        {children}
      </FlagProvider>
    );

    const { result } = renderHook(() => useFlag("feature_a"), { wrapper });
    expect(result.current).toBe(true);

    const { result: resultB } = renderHook(() => useFlag("feature_b"), { wrapper });
    expect(resultB.current).toBe(false);

    const { result: resultC } = renderHook(() => useFlag("unknown"), { wrapper });
    expect(resultC.current).toBe(false);
  });

  it("works with default values", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <FlagProvider initialFlags={{}}>
        {children}
      </FlagProvider>
    );

    const { result } = renderHook(() => useFlag("unknown", true), { wrapper });
    expect(result.current).toBe(true);
  });
});
