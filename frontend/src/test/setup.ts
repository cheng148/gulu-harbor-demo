import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

if (!globalThis.crypto?.randomUUID) {
  vi.stubGlobal("crypto", { randomUUID: () => "test-random-id" });
}

afterEach(() => cleanup());
