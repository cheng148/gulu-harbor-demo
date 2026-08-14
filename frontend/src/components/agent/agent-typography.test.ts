import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("咕噜港全局字体与选宠页字号", () => {
  it("全站正文沿用选宠页标题字体", () => {
    const css = readFileSync(resolve(process.cwd(), "src/app/globals.css"), "utf8");

    expect(css).toMatch(/body\{[^}]*font-family:var\(--title\)/);
    expect(css).toMatch(/button,input,textarea\{font:inherit\}/);
  });

  it("快捷选项文字在按钮内居中", () => {
    const css = readFileSync(resolve(process.cwd(), "src/app/agent/agent.css"), "utf8");

    expect(css).toMatch(/\.answer-pills button\{[^}]*display:grid[^}]*place-items:center[^}]*text-align:center/);
  });

  it("当前问题引导语使用清晰可读的正文级字号", () => {
    const css = readFileSync(resolve(process.cwd(), "src/app/agent/agent.css"), "utf8");

    expect(css).toMatch(/\.current-question small\{[^}]*font-size:14px/);
  });
});
