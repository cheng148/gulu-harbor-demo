import { expect, test } from "@playwright/test";

test("模型或网络失败时保留已有会话并提供原地重试", async ({ page }) => {
  await page.goto("/agent");
  await expect(page.getByRole("region", { name: "选宠对话" })).toBeVisible();
  const welcome = page.locator(".assistant-message").first();
  const welcomeText = await welcome.textContent();

  await page.route("**/api/v1/conversations/*/messages", async (route) => {
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "MODEL_UNAVAILABLE",
          message: "选宠搭子暂时没有回应，请稍后再试。",
          retryable: true,
          details: {},
        },
        meta: { requestId: "e2e-model-unavailable" },
      }),
    });
  });

  await page.getByLabel("用自己的话回答").fill("我想认识一只猫。" );
  await page.getByRole("button", { name: "发送给咕噜" }).click();

  await expect(page.locator(".session-error")).toContainText("选宠搭子暂时没有回应");
  await expect(page.getByRole("button", { name: "再试一次" })).toBeVisible();
  await expect(welcome).toHaveText(welcomeText ?? "");
  await expect(page.locator(".current-question")).toBeVisible();
  const sessionReference = await page.evaluate(() => localStorage.getItem("gulu-harbor.session.v1"));
  expect(sessionReference).toBeTruthy();
});
