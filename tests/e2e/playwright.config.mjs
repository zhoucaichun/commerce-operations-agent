import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "web.spec.mjs",
  use: { baseURL: "http://127.0.0.1:8001", browserName: "chromium", channel: process.platform === "win32" ? "msedge" : undefined, headless: true },
  webServer: {
    command: "python -m uvicorn commerce_agent.api:app --host 127.0.0.1 --port 8001",
    cwd: "../..",
    env: { PYTHONPATH: "src/backend" },
    url: "http://127.0.0.1:8001/health",
    reuseExistingServer: false,
  },
});
