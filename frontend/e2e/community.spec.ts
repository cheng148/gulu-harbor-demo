import { expect, test } from "@playwright/test";

test("从首页进入社区，体验本地点赞、详情和发帖受限提示", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/");
  await page.getByRole("link", { name: "社区" }).click();
  await expect(page).toHaveURL(/\/community$/);
  await expect(page.getByRole("heading", { name: "社区" })).toBeVisible();
  await expect(page.locator("article").first().locator("p").first()).toHaveCSS("font-size", "11px");
  await expect(page.locator("article").first().locator("small").first()).toHaveCSS("font-size", "10px");

  await page.getByRole("button", { name: "点赞小麦来到家的第30天" }).click();
  await expect(page.getByRole("button", { name: "取消点赞小麦来到家的第30天" })).toBeVisible();

  await page.getByRole("button", { name: "查看小麦来到家的第30天详情" }).click();
  await expect(page.getByRole("dialog", { name: "小麦来到家的第30天" })).toContainText("慢慢熟悉彼此就很好");
  await page.getByRole("button", { name: "关闭帖子详情" }).click();

  await page.getByRole("button", { name: "发布动态" }).click();
  await expect(page.getByRole("dialog", { name: "这项功能还在准备中" })).toContainText("Demo演示功能，暂未开放。");
  await expect(page.getByText(/发布成功/)).toHaveCount(0);
  expect(consoleErrors).toEqual([]);
});
