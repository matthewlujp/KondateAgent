#!/usr/bin/env python3
"""Test language settings interactions"""

from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate
    page.goto('http://localhost:5175/settings', wait_until='networkidle')
    print("✓ Page loaded")

    # Wait a bit for state to load
    time.sleep(2)

    # Check initial state
    english_checkbox = page.locator('text=English').locator('..').locator('input[type="checkbox"]')
    japanese_checkbox = page.locator('text=日本語').locator('..').locator('input[type="checkbox"]').nth(1)

    print(f"\nInitial state:")
    print(f"  English checkbox: {'checked' if english_checkbox.is_checked() else 'unchecked'}")
    print(f"  Japanese checkbox: {'checked' if japanese_checkbox.is_checked() else 'unchecked'}")

    # Click English checkbox
    print("\nClicking English checkbox...")
    english_checkbox.click()
    time.sleep(1)

    print(f"After click:")
    print(f"  English checkbox: {'checked' if english_checkbox.is_checked() else 'unchecked'}")

    # Take screenshot
    page.screenshot(path='/tmp/settings_after_click.png', full_page=True)
    print("\n✓ Screenshot saved to /tmp/settings_after_click.png")

    # Click Japanese display language button
    print("\nClicking Japanese display language button...")
    page.locator('button:has-text("日本語")').first.click()
    time.sleep(2)

    page.screenshot(path='/tmp/settings_japanese.png', full_page=True)
    print("✓ Screenshot saved to /tmp/settings_japanese.png")

    # Check if UI changed to Japanese
    title = page.locator('h1').text_content()
    print(f"\nPage title after switching: {title}")

    browser.close()
