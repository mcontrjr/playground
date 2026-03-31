import { test, expect } from "@playwright/test";

test.describe("Validation & edge cases", () => {
  test("shows error for unknown name", async ({ page }) => {
    await page.goto("/rsvp");
    await page.getByPlaceholder("as written on your invitation").fill("ZZZZZUNKNOWN");
    await page.getByRole("button", { name: /find/i }).click();
    await expect(page.getByText(/couldn't find/i)).toBeVisible();
  });

  test("confirm button is disabled until all meals selected", async ({ page }) => {
    await page.goto("/rsvp/meals?partyId=1&guests=Alice||Bob");
    const btn = page.getByRole("button", { name: /confirm rsvp/i });
    await expect(btn).toBeDisabled();
    await page.getByRole("button", { name: "Steak" }).first().click();
    // Still disabled — Bob hasn't chosen
    await expect(btn).toBeDisabled();
    await page.getByRole("button", { name: "Fish" }).nth(1).click();
    await expect(btn).toBeEnabled();
  });

  test("guest stepper respects min=1 and max from party", async ({ page }) => {
    await page.goto("/rsvp/guests?partyId=1&partyName=Test&maxGuests=2&members=Alice");
    const minus = page.getByLabel("Remove guest");
    const plus  = page.getByLabel("Add guest");
    await expect(minus).toBeDisabled();    // already at min=1
    await plus.click();
    await expect(plus).toBeDisabled();     // now at max=2
  });

  test("name input requires at least 2 characters", async ({ page }) => {
    await page.goto("/rsvp");
    await page.getByPlaceholder("as written on your invitation").fill("A");
    await page.getByRole("button", { name: /find/i }).click();
    // Browser native validation prevents submission
    const input = page.getByPlaceholder("as written on your invitation");
    await expect(input).toBeFocused();
  });
});
