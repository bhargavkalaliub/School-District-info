from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://html.duckduckgo.com/html/?q="Los+Angeles+Unified+School+District"+"Director+of+Food+Services"+email')
    time.sleep(2)
    content = page.content()
    soup = BeautifulSoup(content, 'html.parser')
    results = soup.find_all('a', class_='result__snippet')
    for r in results:
        print(r.text)
    browser.close()
