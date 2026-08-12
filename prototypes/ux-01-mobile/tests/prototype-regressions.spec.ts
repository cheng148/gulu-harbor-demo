import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "开始聊聊" }).click();
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
