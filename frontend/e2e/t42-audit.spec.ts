import { expect, type Page, test } from "@playwright/test";
import path from "node:path";

const auditRoot = path.resolve(process.cwd(), "../docs/qa/screenshots/t42");
const routes = [
  { path: "/", name: "home" },
  { path: "/agent", name: "agent" },
  { path: "/market", name: "market" },
  { path: "/supplies", name: "supplies" },
  { path: "/community", name: "community" },
  { path: "/me", name: "me" },
  { path: "/membership", name: "membership" },
] as const;

function observeRuntime(page: Page) {
  const consoleProblems: string[] = [];
  const failedResponses: string[] = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      consoleProblems.push(`${message.type()}: ${message.text()}`);
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${response.url()}`);
    }
  });
  return { consoleProblems, failedResponses };
}

test("手机和桌面主要页面可重排且具有基本可访问结构", async ({ page }, testInfo) => {
  const runtime = observeRuntime(page);
  const shouldCaptureEveryRoute = testInfo.project.name === "mobile-chromium";

  for (const [index, route] of routes.entries()) {
    const consoleProblemStart = runtime.consoleProblems.length;
    const failedResponseStart = runtime.failedResponses.length;
    await page.goto(route.path);
    await expect(page.locator("main")).toBeVisible();
    await page.waitForLoadState("networkidle");

    if (shouldCaptureEveryRoute || route.name === "home" || route.name === "agent") {
      await page.screenshot({
        path: path.join(
          auditRoot,
          testInfo.project.name,
          `${String(index + 1).padStart(2, "0")}-${route.name}.png`,
        ),
        fullPage: true,
        caret: "initial",
      });
    }

    const layout = await page.evaluate(() => ({
      viewportWidth: document.documentElement.clientWidth,
      pageWidth: document.documentElement.scrollWidth,
      mainCount: document.querySelectorAll("main").length,
      h1Count: document.querySelectorAll("h1").length,
      imagesWithoutAlt: [...document.querySelectorAll("img")].filter(
        (image) => !image.hasAttribute("alt"),
      ).length,
      unnamedControls: [...document.querySelectorAll<HTMLElement>("button, a[href], input, textarea")]
        .filter((element) => element.getClientRects().length > 0)
        .filter((element) => {
          const labelledBy = element.getAttribute("aria-labelledby");
          const labelledByText = labelledBy
            ? document.getElementById(labelledBy)?.textContent?.trim()
            : "";
          const nativeLabel =
            element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement
              ? Array.from(element.labels ?? []).map((label) => label.textContent).join(" ").trim()
              : "";
          return !(
            element.getAttribute("aria-label")?.trim() ||
            labelledByText ||
            nativeLabel ||
            element.textContent?.trim() ||
            element.getAttribute("title")?.trim()
          );
        })
        .map((element) => element.outerHTML.slice(0, 160)),
    }));

    expect(layout.pageWidth, `${route.path}不应横向溢出`).toBeLessThanOrEqual(
      layout.viewportWidth + 1,
    );
    expect(layout.mainCount, `${route.path}应有且只有一个main`).toBe(1);
    expect(layout.h1Count, `${route.path}应有且只有一个主标题`).toBe(1);
    expect(layout.imagesWithoutAlt, `${route.path}图片必须声明替代文字`).toBe(0);
    expect(layout.unnamedControls, `${route.path}交互控件必须有可读名称`).toEqual([]);
    expect(runtime.consoleProblems.slice(consoleProblemStart), `${route.path}控制台应无警告或错误`).toEqual([]);
    expect(runtime.failedResponses.slice(failedResponseStart), `${route.path}网络请求应无HTTP错误`).toEqual([]);
  }

  expect(runtime.consoleProblems).toEqual([]);
  expect(runtime.failedResponses).toEqual([]);
});

test("弹窗支持键盘打开、Escape关闭并把焦点还给原按钮", async ({ page }, testInfo) => {
  await page.goto("/community");
  const trigger = page.getByRole("button", { name: "发布动态" });
  await trigger.focus();
  await page.keyboard.press("Enter");

  const dialog = page.getByRole("dialog", { name: "这项功能还在准备中" });
  await expect(dialog).toBeVisible();
  await page.screenshot({
    path: path.join(auditRoot, testInfo.project.name, "08-keyboard-dialog.png"),
    fullPage: true,
    caret: "initial",
  });
  await expect(page.getByRole("button", { name: "关闭" })).toBeFocused();

  await page.keyboard.press("Escape");

  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("核心对话可用中文键盘完成并留下结果页截图", async ({ page }, testInfo) => {
  const runtime = observeRuntime(page);
  const turns = [
    "我想认识一只成年英国短毛猫，偏中等体型和短毛。",
    "工作日能留出一些时间，希望活动量不用太高。",
    "我喜欢安静一点的互动，待在附近陪着就很好。",
    "我能接受规律梳毛和中等花费，没有绝对不能接受的日常负担。",
    "猫狗都不过敏。",
  ];

  await page.goto("/agent");
  for (const answer of turns) {
    const composer = page.getByLabel("用自己的话回答");
    await composer.fill(answer);
    await composer.press("Enter");
  }

  await expect(page).toHaveURL(/\/agent\/results$/);
  await expect(page.getByRole("heading", { name: "从方向到具体伙伴，慢慢认识" })).toBeVisible();
  await page.screenshot({
    path: path.join(auditRoot, testInfo.project.name, "09-recommendation-result.png"),
    fullPage: true,
    caret: "initial",
  });
  expect(runtime.consoleProblems).toEqual([]);
  expect(runtime.failedResponses).toEqual([]);
});

test("320到430像素手机宽度均无横向溢出且底栏保持可用", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium", "手机宽度矩阵只需在移动浏览器项目运行");

  for (const width of [320, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
    const widths = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    }));
    expect(widths.content, `${width}px时不应横向溢出`).toBeLessThanOrEqual(widths.viewport + 1);
    await page.screenshot({
      path: path.join(auditRoot, testInfo.project.name, `10-home-${width}px.png`),
      fullPage: false,
      caret: "initial",
    });
  }
});

test("PWA清单提供安装图标，普通链接无需安装也能进入核心流程", async ({ page, request }) => {
  await page.goto("/");
  const manifestHref = await page.locator('link[rel="manifest"]').getAttribute("href");
  expect(manifestHref).toBeTruthy();

  const response = await request.get(manifestHref!);
  expect(response.ok()).toBeTruthy();
  const manifest = await response.json();
  expect(manifest).toMatchObject({ name: "咕噜港", start_url: "/", display: "standalone" });
  expect(manifest.icons.map((icon: { sizes?: string }) => icon.sizes)).toEqual(
    expect.arrayContaining(["192x192", "512x512"]),
  );

  await page.getByRole("link", { name: "去聊聊" }).click();
  await expect(page).toHaveURL(/\/agent$/);
  await expect(page.getByLabel("用自己的话回答")).toBeVisible();
});
