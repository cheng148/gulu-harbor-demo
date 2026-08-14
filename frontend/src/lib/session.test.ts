import { describe, expect, it } from "vitest";

import {
  clearSessionReference,
  inspectSessionReference,
  loadSessionReference,
  saveSessionReference,
  SESSION_STORAGE_KEY,
} from "./session";

class MemoryStorage implements Pick<Storage, "getItem" | "setItem" | "removeItem"> {
  private readonly values = new Map<string, string>();

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }

  removeItem(key: string) {
    this.values.delete(key);
  }
}

describe("匿名会话本地引用", () => {
  it("只保存会话编号和到期时间", () => {
    const storage = new MemoryStorage();

    saveSessionReference(storage, {
      conversationId: "conv-123",
      expiresAt: "2026-08-14T10:00:00.000Z",
    });

    expect(JSON.parse(storage.getItem(SESSION_STORAGE_KEY) ?? "{}")).toEqual({
      conversationId: "conv-123",
      expiresAt: "2026-08-14T10:00:00.000Z",
    });
    expect(storage.getItem(SESSION_STORAGE_KEY)).not.toMatch(
      /message|profile|api.?key|deepseek|token/i,
    );
  });

  it("未过期时恢复同一个会话引用", () => {
    const storage = new MemoryStorage();
    saveSessionReference(storage, {
      conversationId: "conv-123",
      expiresAt: "2026-08-14T10:00:00.000Z",
    });

    expect(
      loadSessionReference(storage, new Date("2026-08-13T10:00:00.000Z")),
    ).toEqual({
      conversationId: "conv-123",
      expiresAt: "2026-08-14T10:00:00.000Z",
    });
  });

  it("过期或损坏的数据会被清除，不能继续恢复", () => {
    const expiredStorage = new MemoryStorage();
    saveSessionReference(expiredStorage, {
      conversationId: "conv-old",
      expiresAt: "2026-08-13T09:59:59.000Z",
    });

    expect(
      loadSessionReference(expiredStorage, new Date("2026-08-13T10:00:00.000Z")),
    ).toBeNull();
    expect(expiredStorage.getItem(SESSION_STORAGE_KEY)).toBeNull();

    const brokenStorage = new MemoryStorage();
    brokenStorage.setItem(SESSION_STORAGE_KEY, "not-json");
    expect(loadSessionReference(brokenStorage)).toBeNull();
    expect(brokenStorage.getItem(SESSION_STORAGE_KEY)).toBeNull();
  });

  it("能区分没有旧会话和旧会话刚刚过期", () => {
    const storage = new MemoryStorage();
    expect(inspectSessionReference(storage, new Date("2026-08-13T10:00:00.000Z"))).toEqual({ status: "missing" });

    saveSessionReference(storage, {
      conversationId: "conv-expired",
      expiresAt: "2026-08-13T09:59:59.000Z",
    });
    expect(inspectSessionReference(storage, new Date("2026-08-13T10:00:00.000Z"))).toEqual({ status: "expired" });
    expect(storage.getItem(SESSION_STORAGE_KEY)).toBeNull();
  });
  it("主动清除后不再恢复旧会话", () => {
    const storage = new MemoryStorage();
    saveSessionReference(storage, {
      conversationId: "conv-reset",
      expiresAt: "2026-08-14T10:00:00.000Z",
    });

    clearSessionReference(storage);

    expect(storage.getItem(SESSION_STORAGE_KEY)).toBeNull();
  });
});
