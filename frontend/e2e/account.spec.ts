import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => window.localStorage.clear());
});

test("全站底栏进入我的，并完成会员展示与开通受限流程", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.getByRole("link", { name: "我的" }).click();
  await expect(page).toHaveURL(/\/me$/);
  await expect(page.getByRole("heading", { name: "我的港湾" })).toBeVisible();
  await expect(page.getByRole("link", { name: "我的" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByText("Demo不创建真实订单")).toHaveCSS("font-size", "10px");
  await expect(page.getByText(/收藏、点赞和购物车仅保存在/)).toHaveCSS("font-size", "10px");

  await page.getByRole("link", { name: "进入会员中心" }).click();
  await expect(page).toHaveURL(/\/membership$/);
  await page.getByRole("button", { name: "预览会员状态" }).click();
  await expect(page.getByText("当前为会员展示状态")).toBeVisible();
  await page.getByRole("button", { name: "选择年度会员" }).click();
  await page.getByRole("button", { name: "确认开通年度会员" }).click();
  await expect(page.getByText("Demo演示功能，暂未开放。")).toBeVisible();
  await expect(page.getByText(/开通成功|支付成功|订单号/)).toHaveCount(0);

  await page.getByRole("button", { name: "知道了" }).click();
  await page.getByRole("link", { name: "社区" }).click();
  await expect(page).toHaveURL(/\/community$/);
  await page.getByRole("link", { name: "选宠" }).click();
  await expect(page).toHaveURL(/\/agent$/);
  expect(consoleErrors).toEqual([]);
});

test("宠物市场和用品页也保留统一底栏", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  await expect(page.getByRole("link", { name: "我的" })).toHaveAttribute("href", "/me");

  await page.goto("/supplies");
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  await expect(page.getByRole("link", { name: "社区" })).toHaveAttribute("href", "/community");
});
