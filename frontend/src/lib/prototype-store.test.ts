import { beforeEach, describe, expect, it } from "vitest";

import prototypeData from "../data/prototype.json";
import { PROTOTYPE_STORAGE_KEY, createPrototypeStore } from "./prototype-store";

describe("T36 原型数据边界", () => {
  beforeEach(() => window.localStorage.clear());

  it("静态数据明确是模拟数据且不包含Agent内部结果", () => {
    expect(prototypeData.meta.isSimulated).toBe(true);
    expect(prototypeData.meta.disclosure).toContain("Demo虚拟数据");
    const serialized = JSON.stringify(prototypeData);
    expect(serialized).not.toMatch(/internalScore|conversationId|profileSummary/);
  });

  it("原型交互状态使用独立存储键，不会写入Agent会话", () => {
    const store = createPrototypeStore(window.localStorage);

    store.toggleFavorite("pet-xiaomai");
    store.togglePostLike("post-1");
    store.addCartItem("supply-1");
    store.setDemoMembership(true);

    expect(store.load()).toEqual({
      favoriteIds: ["pet-xiaomai"],
      likedPostIds: ["post-1"],
      cart: { "supply-1": 1 },
      demoMembership: true,
    });
    expect(window.localStorage.getItem(PROTOTYPE_STORAGE_KEY)).not.toBeNull();
    expect(window.localStorage.getItem("gulu-harbor.session.v1")).toBeNull();
  });

  it("损坏或越界的本地原型状态会安全回到默认值", () => {
    window.localStorage.setItem(
      PROTOTYPE_STORAGE_KEY,
      JSON.stringify({ favoriteIds: ["ok", 3], likedPostIds: [], cart: {}, demoMembership: false }),
    );

    expect(createPrototypeStore(window.localStorage).load()).toEqual({
      favoriteIds: [],
      likedPostIds: [],
      cart: {},
      demoMembership: false,
    });
  });
});
