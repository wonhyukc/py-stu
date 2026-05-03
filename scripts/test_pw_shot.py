from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(
        "https://gemini.google.com/share/952fa82ead2e", wait_until="domcontentloaded"
    )
    page.wait_for_timeout(5000)
    page.screenshot(path="screenshot.png")

    # get all text inside the main conversation container if it exists
    # we can try to get text of all div with text
    print("Page Title:", page.title())
    browser.close()
