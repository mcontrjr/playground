import { test, expect } from "@playwright/test";

test.describe("Admin protection", () => {
  test("redirects without password", async ({ page }) => {
    await page.goto("/admin");
    // Should show empty password state, not data
    await expect(page.getByText("RSVP Summary")).not.toBeVisible();
  });

  test("export CSV requires auth header", async ({ request }) => {
    const res = await request.get("/api/admin/export");
    expect(res.status()).toBe(401);
  });
});
