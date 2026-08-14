import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "选宠" }).click();
  await page.getByRole("button", { name: "开始聊聊" }).click();
});

test("first visit opens the platform home with the breed hot list", async ({ page }) => {
  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.getByRole("button", { name: "首页" })).toHaveClass(/on/);
  await expect(page.getByText("本期热门品种")).toBeVisible();
  await expect(page.getByRole("heading", { name: "布偶猫", exact: true })).toBeVisible();
  await expect(page.getByText("近30天模拟成交 234")).toBeVisible();
});

test("chat header stays fixed while conversation scrolls", async ({ page }) => {
  const header = page.getByTestId("chat-fixed-header");
  const scroll = page.getByTestId("mobile-scroll");
  const before = await header.boundingBox();
  await scroll.evaluate((element) => { element.scrollTop = 300; });
  const after = await header.boundingBox();
  expect(after?.y).toBe(before?.y);
});

test("reset starts the conversation from the initial description", async ({ page }) => {
  await page.getByRole("button", { name: "猫狗都可以" }).click();
  await page.getByRole("button", { name: "发送给咕噜" }).click();
  await page.getByRole("button", { name: "重新开始" }).click();
  await page.getByRole("button", { name: "确认重置" }).click();
  await expect(page.getByRole("heading", { name: "你希望遇见一位怎样的小伙伴？" })).toBeVisible();
});

test("simulated keyboard types, deletes and dismisses", async ({ page }) => {
  await page.getByPlaceholder("比如：白天要上班，晚上可以陪它玩一会儿……").click();
  await page.getByTestId("keyboard-key-q").click();
  await expect(page.getByPlaceholder("比如：白天要上班，晚上可以陪它玩一会儿……")).toHaveValue("q");
  await page.getByTestId("keyboard-backspace").click();
  await expect(page.getByPlaceholder("比如：白天要上班，晚上可以陪它玩一会儿……")).toHaveValue("");
  await page.getByTestId("keyboard-dismiss").click();
  await expect(page.getByTestId("keyboard-dock")).toHaveAttribute("data-visible", "false");
});

test("profile has a portrait and multiple care dimensions", async ({ page }) => {
  await page.getByRole("button", { name: "猫狗都可以" }).click();
  await page.getByRole("button", { name: "发送给咕噜" }).click();
  await page.getByRole("button", { name: "看看目前记住了什么" }).click();
  await expect(page.getByRole("img", { name: "你的相处画像卡通形象" })).toBeVisible();
  await expect(page.getByText("清洁与掉毛")).toBeVisible();
  await expect(page.getByText("活动与外出")).toBeVisible();
  await expect(page.getByText("日常照护")).toBeVisible();
});

test("chat title follows the current stage and nav uses one component style", async ({ page }) => {
  await expect(page.getByTestId("chat-stage-title")).toHaveText("先认识一下你");
  await page.getByRole("button", { name: "猫狗都可以" }).click();
  await page.getByRole("button", { name: "发送给咕噜" }).click();
  await expect(page.getByTestId("chat-stage-title")).toHaveText("了解你的日常");
  const navButtons = page.locator(".nav button");
  await expect(navButtons).toHaveCount(4);
  await expect(navButtons.nth(1)).toHaveClass(/on/);
});

test("pet tab always keeps the paw icon and nav geometry", async ({ page }) => {
  const petButton = page.getByRole("button", { name: "选宠" });
  await expect(petButton.locator("[data-icon=pet-paw]")).toBeVisible();
  const before = await page.locator(".nav").boundingBox();
  await page.getByRole("button", { name: "首页" }).click();
  const after = await page.locator(".nav").boundingBox();
  expect(after).toEqual(before);
  await expect(page.getByRole("button", { name: "选宠" }).locator("[data-icon=pet-paw]")).toBeVisible();
});

test("reset action sits at the bottom of the conversation, not in the header", async ({ page }) => {
  await expect(page.getByTestId("chat-fixed-header").getByRole("button", { name: "重新开始" })).toHaveCount(0);
  await expect(page.locator(".chat-reset-action")).toHaveText("重新开始");
});

test("real touch devices expose native text input mode", async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(navigator, "maxTouchPoints", { value: 5 }));
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "选宠" }).click();
  await page.getByRole("button", { name: "开始聊聊" }).click();
  await page.getByPlaceholder("比如：白天要上班，晚上可以陪它玩一会儿……").click();
  await expect(page.getByTestId("keyboard-dock")).toHaveAttribute("data-native-input", "true");
});

test("home opens breed categories before two individual pets", async ({ page }) => {
  await page.getByRole("button", { name: "首页" }).click();
  await page.getByRole("button", { name: "逛宠物市场" }).click();
  await expect(page.getByRole("heading", { name: "宠物市场" })).toBeVisible();
  await expect(page.getByRole("article", { name: "布偶猫品种" })).toBeVisible();
  await expect(page.getByRole("article", { name: /宠物档案/ })).toHaveCount(0);
  await page.getByRole("button", { name: "查看布偶猫的模拟在售宠物" }).click();
  await expect(page.getByRole("article", { name: /宠物档案/ })).toHaveCount(2);
  await expect(page.getByRole("article", { name: "奶盖宠物档案" })).toBeVisible();
  await expect(page.getByRole("article", { name: "云朵宠物档案" })).toBeVisible();
  await expect(page.getByRole("article", { name: "奶盖宠物档案" })).toContainText("海风宠物生活馆");
  await page.getByRole("button", { name: "收藏奶盖" }).click();
  await expect(page.getByRole("button", { name: "取消收藏奶盖" })).toBeVisible();
});

test("supplies use a local demo cart and block real checkout", async ({ page }) => {
  await page.getByRole("button", { name: "首页" }).click();
  await page.getByRole("button", { name: "看看宠物用品" }).click();
  await expect(page.getByRole("heading", { name: "宠物用品" })).toBeVisible();
  await expect(page.getByTestId("fixed-cart-bar")).toHaveCount(0);
  await page.getByRole("button", { name: "清洁护理" }).click();
  await page.getByRole("button", { name: "把温和免洗清洁手套加入模拟购物车" }).click();
  await expect(page.getByRole("status", { name: "加入购物车反馈" })).toHaveText("已加入模拟购物车，本机共有 1 件用品");
  const cartBar = page.getByTestId("fixed-cart-bar");
  await expect(cartBar).toHaveCSS("position", "fixed");
  const before = await cartBar.boundingBox();
  await page.getByTestId("mobile-scroll").evaluate(element => { element.scrollTop = element.scrollHeight; });
  const after = await cartBar.boundingBox();
  expect(after?.y).toBe(before?.y);
  await cartBar.getByRole("button", { name: "模拟结算" }).click();
  await expect(page.getByText("Demo演示功能，暂未开放。")).toBeVisible();
  await expect(page.getByText(/下单成功|支付成功/)).toHaveCount(0);
});

test("community supports demo posts, local reactions and a blocked publisher", async ({ page }) => {
  await page.getByRole("button", { name: "社区" }).click();

  await expect(page.getByRole("heading", { name: "社区", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "社区" })).toHaveClass(/on/);
  await expect(page.getByRole("article")).toHaveCount(3);
  await expect(page.locator(".community-open p").first()).toHaveCSS("font-size", "11px");
  await expect(page.locator(".community-card header small").first()).toHaveCSS("font-size", "10px");

  await page.getByRole("button", { name: "点赞小麦来到家的第30天" }).click();
  await expect(page.getByRole("button", { name: "取消点赞小麦来到家的第30天" })).toBeVisible();
  await page.getByRole("button", { name: "收藏雨天也能玩的嗅闻小游戏" }).click();
  await expect(page.getByRole("button", { name: "取消收藏雨天也能玩的嗅闻小游戏" })).toBeVisible();

  await page.getByRole("button", { name: "查看小麦来到家的第30天详情" }).click();
  await expect(page.getByRole("heading", { name: "小麦来到家的第30天" })).toBeVisible();
  await expect(page.getByText("刚到家时总躲在沙发后面")).toBeVisible();
  await page.getByRole("button", { name: "收起详情" }).click();

  await page.getByRole("button", { name: "发布动态" }).click();
  await expect(page.getByText("Demo演示功能，暂未开放。")).toBeVisible();
  await expect(page.getByText("发布成功")).toHaveCount(0);
});

test("my harbor and membership remain local Demo experiences", async ({ page }) => {
  await page.getByRole("button", { name: "我的" }).click();

  await expect(page.getByRole("heading", { name: "我的港湾" })).toBeVisible();
  await expect(page.getByRole("button", { name: "我的", exact: true })).toHaveClass(/on/);
  await expect(page.getByText("无账户Demo体验")).toBeVisible();
  await expect(page.getByLabel("本机收藏数量")).toContainText("0");
  await expect(page.locator(".account-menu small").first()).toHaveCSS("font-size", "10px");
  await expect(page.locator(".account-local-note")).toHaveCSS("font-size", "10px");

  await page.getByRole("button", { name: "进入会员中心" }).click();
  await expect(page.locator(".apphead").getByText("会员中心", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "预览会员状态" }).click();
  await expect(page.getByText("当前为会员展示状态")).toBeVisible();
  await page.getByRole("button", { name: "选择年度会员" }).click();
  await page.getByRole("button", { name: "确认开通年度会员" }).click();
  await expect(page.getByText("Demo演示功能，暂未开放。")).toBeVisible();
  await expect(page.getByText(/开通成功|支付成功|订单号/)).toHaveCount(0);
});
