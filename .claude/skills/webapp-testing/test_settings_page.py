#!/usr/bin/env python3
"""Test settings page and capture console errors"""

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Capture console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append({
        "type": msg.type,
        "text": msg.text
    }))

    # Capture errors
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    try:
        print("Navigating to settings page...")
        page.goto('http://localhost:5175/settings', wait_until='networkidle', timeout=10000)

        # Take screenshot
        page.screenshot(path='/tmp/settings_page.png', full_page=True)
        print("Screenshot saved to /tmp/settings_page.png")

        # Get page title
        title = page.title()
        print(f"Page title: {title}")

        # Check if there's any visible content
        body_text = page.locator('body').text_content()
        print(f"\nVisible text length: {len(body_text) if body_text else 0}")

        # Print console messages
        if console_messages:
            print("\n=== Console Messages ===")
            for msg in console_messages:
                print(f"[{msg['type']}] {msg['text']}")

        # Print errors
        if errors:
            print("\n=== Page Errors ===")
            for error in errors:
                print(error)

        # Try to find specific elements
        print("\n=== Element Check ===")
        header = page.locator('header').count()
        print(f"Header elements: {header}")

        settings_title = page.locator('h1:has-text("Settings")').count()
        print(f"Settings title: {settings_title}")

        language_section = page.locator('text=Language').count()
        print(f"Language section: {language_section}")

    except Exception as e:
        print(f"Error: {e}")
        page.screenshot(path='/tmp/settings_error.png', full_page=True)
        print("Error screenshot saved to /tmp/settings_error.png")
    finally:
        browser.close()
