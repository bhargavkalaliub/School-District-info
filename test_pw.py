from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://duckduckgo.com/?q=site:lausd.org+food+service+director+email&t=h_&ia=web')
    time.sleep(3)
    content = page.content()
    print("lausd.org" in content)
    browser.close()
