import { expect, test } from "@playwright/test";

test("web flow submits a synthetic product query", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "3C Commerce Operations Agent" })).toBeVisible();
  await page.getByRole("button", { name: "查询商品" }).click();
  await page.getByRole("button", { name: "提交安全查询" }).click();
  await expect(page.locator("#status")).toHaveText("completed");
  await expect(page.locator("#answer")).toContainText("模拟商品目录");
});

test("web flow explains an authentication failure", async ({ page }) => {
  await page.route("**/api/v1/chat", (route) => route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Bearer token is required" }) }));
  await page.goto("/");
  await page.locator("#message").fill("charger");
  await page.getByRole("button", { name: "提交安全查询" }).click();
  await expect(page.locator("#status")).toHaveText("请求失败");
  await expect(page.locator("#answer")).toContainText("身份验证未通过");
});
