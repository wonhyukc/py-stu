from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(
        "https://gemini.google.com/share/952fa82ead2e",
        wait_until="networkidle",
        timeout=60000,
    )
    page.screenshot(path="screenshot.png")
    print(page.url)
    browser.close()
