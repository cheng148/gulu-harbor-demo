import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "mobile-chromium",
      use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
    },
    {
      name: "desktop-chromium",
      use: { viewport: { width: 1280, height: 900 } },
    },
  ],
  webServer: [
    {
      command: "uv run uvicorn app.demo:app --host 127.0.0.1 --port 8010",
      cwd: "../backend",
      url: "http://127.0.0.1:8010/health",
      reuseExistingServer: false,
      env: { MODEL_PROVIDER: "mock", DATABASE_PATH: "./var/e2e.db" },
    },
    {
      command: "pnpm dev --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      env: { API_INTERNAL_BASE_URL: "http://127.0.0.1:8010" },
    },
  ],
});
