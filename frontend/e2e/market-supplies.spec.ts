import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => window.localStorage.clear());
});

test("首页展示品种热榜，市场按品种进入两只个体档案", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/");
  const hotBreeds = page.getByRole("region", { name: "本期热门品种" });
  await expect(hotBreeds).toContainText("布偶猫");
  await expect(hotBreeds).toContainText("近30天模拟成交 234");

  await page.getByRole("link", { name: "逛宠物市场" }).click();
  await expect(page).toHaveURL(/\/market$/);
  await expect(page.getByRole("heading", { name: "宠物市场" })).toBeVisible();
  await expect(page.getByRole("article", { name: "布偶猫品种" })).toBeVisible();
  await expect(page.getByRole("article", { name: /宠物档案/ })).toHaveCount(0);

  await page.getByRole("button", { name: "查看布偶猫的模拟在售宠物" }).click();
  await expect(page.getByRole("heading", { name: "布偶猫的小伙伴" })).toBeVisible();
  const petCards = page.getByRole("article", { name: /宠物档案/ });
  await expect(petCards).toHaveCount(2);
  await expect(petCards.first()).toContainText(/海风宠物生活馆|灯塔伙伴宠物屋/);
  await expect(petCards.nth(1)).toContainText(/海风宠物生活馆|灯塔伙伴宠物屋/);
  await expect(petCards.first()).not.toContainText(/销量|好评率/);
  await expect(petCards.nth(1)).not.toContainText(/销量|好评率/);

  await page.getByRole("button", { name: "收藏奶盖" }).click();
  await expect(page.getByRole("button", { name: "取消收藏奶盖" })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "查看布偶猫的模拟在售宠物" }).click();
  await expect(page.getByRole("button", { name: "取消收藏奶盖" })).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test("购物车为空时隐藏，加入后给出反馈并固定在页面底部", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/supplies");
  await expect(page.getByRole("heading", { name: "宠物用品" })).toBeVisible();
  await expect(page.getByTestId("fixed-cart-bar")).toHaveCount(0);

  await page.getByRole("button", { name: "清洁护理" }).click();
  await page.getByRole("button", { name: "把温和免洗清洁手套加入模拟购物车" }).click();
  await expect(page.getByRole("status", { name: "加入购物车反馈" })).toHaveText("已加入模拟购物车，本机共有 1 件用品");

  const cartBar = page.getByTestId("fixed-cart-bar");
  await expect(cartBar).toBeVisible();
  await expect(cartBar).toHaveCSS("position", "fixed");
  const before = await cartBar.boundingBox();
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  const after = await cartBar.boundingBox();
  expect(after?.y).toBe(before?.y);

  await cartBar.getByRole("button", { name: "打开模拟购物车" }).click();
  await expect(page.getByRole("dialog", { name: "模拟购物车" })).toContainText("温和免洗清洁手套");
  await page.getByRole("button", { name: "模拟结算" }).click();
  await expect(page.getByRole("dialog", { name: "这项功能还在准备中" })).toContainText("Demo演示功能，暂未开放。");
  await expect(page.getByText(/下单成功|支付成功/)).toHaveCount(0);
  expect(consoleErrors).toEqual([]);
});
