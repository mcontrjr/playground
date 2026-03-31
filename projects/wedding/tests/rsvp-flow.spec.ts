import { test, expect } from "@playwright/test";

// These must exist in your test database
const KNOWN_NAME    = "Alice Johnson";
const PARTY_NAME    = "The Johnson Family";

test.describe("RSVP happy path", () => {
  test("completes full flow from landing to confirmation", async ({ page }) => {
    // Step 1 — Landing
    await page.goto("/rsvp");
    await expect(page.getByText("R S V P")).toBeVisible();

    // Search for name
    await page.getByPlaceholder("as written on your invitation").fill(KNOWN_NAME);
    await page.getByRole("button", { name: /find my invitation/i }).click();

    // Step 2 — Party selection
    await expect(page.getByText(PARTY_NAME)).toBeVisible();
    await page.getByText(PARTY_NAME).click();

    // Step 3 — Guests
    await expect(page).toHaveURL(/\/rsvp\/guests/);
    // Increase guest count to 2
    await page.getByLabel("Add guest").click();
    // Fill second guest name
    const inputs = page.getByRole("textbox");
    await inputs.nth(1).fill("Bob Johnson");
    await page.getByRole("button", { name: /continue/i }).click();

    // Step 4 — Meals
    await expect(page).toHaveURL(/\/rsvp\/meals/);
    // Select meal for each guest
    await page.getByRole("button", { name: "Steak" }).first().click();
    await page.getByRole("button", { name: "Fish"  }).nth(1).click();

    // Confirm is enabled now
    const confirmBtn = page.getByRole("button", { name: /confirm rsvp/i });
    await expect(confirmBtn).toBeEnabled();
    await confirmBtn.click();

    // Step 5 — Confirmation
    await expect(page).toHaveURL(/\/rsvp\/confirm/);
    await expect(page.getByText(/you're confirmed/i)).toBeVisible();
    await expect(page.getByText(/can't wait to celebrate/i)).toBeVisible();
    await expect(page.getByText("Apple / Outlook Calendar")).toBeVisible();
    await expect(page.getByText("Google Calendar")).toBeVisible();
  });
});
