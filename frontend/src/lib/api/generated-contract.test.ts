import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("OpenAPI生成类型", () => {
  it("包含会话接口且不泄漏密钥或内部匹配分", () => {
    const generated = readFileSync(
      resolve(process.cwd(), "src/lib/api/generated.ts"),
      "utf8",
    );

    expect(generated).toContain('"/api/v1/conversations"');
    expect(generated).toContain("conversationId");
    expect(generated).toContain("expiresAt");
    expect(generated).not.toMatch(/DEEPSEEK_API_KEY|apiKey|internalScore|matchScore/);
  });
});
