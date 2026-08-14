import { expect, test } from "@playwright/test";

const approvedTurns = [
  "我想认识一只成年英国短毛猫，偏中等体型和短毛。",
  "工作日能留出一些时间，希望活动量不用太高。",
  "我喜欢安静一点的互动，待在附近陪着就很好。",
  "我能接受规律梳毛和中等花费，没有绝对不能接受的日常负担。",
  "猫狗都不过敏。",
] as const;

test("完成5轮动态对话，看到双层推荐并修改条件重新推荐", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "不知道选谁？先从你的生活聊起" })).toBeVisible();
  await page.getByRole("link", { name: "去聊聊" }).click();
  await expect(page).toHaveURL(/\/agent$/);

  for (const turn of approvedTurns) {
    await page.getByLabel("用自己的话回答").fill(turn);
    await page.getByRole("button", { name: "发送给咕噜" }).click();
  }

  await expect(page).toHaveURL(/\/agent\/results$/);
  await expect(page.getByRole("heading", { name: "先看适合你的方向" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "再认识具体的小伙伴" })).toBeVisible();
  expect(await page.locator(".direction-card").count()).toBeGreaterThan(0);
  expect(await page.locator(".result-pet-card").count()).toBeGreaterThan(0);

  const profilePatch = page.waitForResponse((response) =>
    response.request().method() === "PATCH" && response.url().endsWith("/profile"),
  );
  await page.getByRole("button", { name: "修改条件再看看" }).click();
  await page.getByRole("button", { name: /互动节奏/ }).click();
  await page.getByRole("button", { name: "喜欢经常一起玩" }).click();
  await page.getByRole("button", { name: "保存并重新推荐" }).click();

  const patchResponse = await profilePatch;
  expect(patchResponse.ok()).toBeTruthy();
  const patchPayload = await patchResponse.json();
  expect(patchPayload.data.recommendation).toBeTruthy();
  expect(patchPayload.data.recommendationChanges.length).toBeGreaterThan(0);
  await expect(page.getByRole("status")).toContainText("已经更新好啦");
  expect(consoleErrors).toEqual([]);
});

test("页面提供可添加到手机主屏幕的基础清单", async ({ page, request }) => {
  await page.goto("/");
  const manifestHref = await page.locator('link[rel="manifest"]').getAttribute("href");
  expect(manifestHref).toBeTruthy();

  const response = await request.get(manifestHref!);
  expect(response.ok()).toBeTruthy();
  const manifest = await response.json();
  expect(manifest).toMatchObject({
    name: "咕噜港",
    start_url: "/",
    display: "standalone",
  });
  expect(manifest.icons.length).toBeGreaterThan(0);
});
