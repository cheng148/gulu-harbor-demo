import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("咕噜港手机App外壳", () => {
  it("在电脑上仍保持手机App宽度和两列卡片", () => {
    const css = readFileSync(resolve(process.cwd(), "src/app/globals.css"), "utf8");

    expect(css).toContain("--app-width:430px");
    expect(css).toContain("max-width:var(--app-width)");
    expect(css).not.toContain("width:min(100%,1180px)");
    expect(css).not.toContain(".pet-grid{grid-template-columns:repeat(4,minmax(0,1fr))");
  });
});
