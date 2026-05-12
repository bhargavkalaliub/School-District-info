from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://duckduckgo.com/?q="Los+Angeles+Unified+School+District"+"Director+of+Food+Services"+email&t=h_&ia=web')
    time.sleep(3)
    content = page.content()
    soup = BeautifulSoup(content, 'html.parser')
    results = soup.find_all('a', {'data-testid': 'result-title-a'})
    for r in results:
        print(r.text, r.get('href'))

    snippets = soup.find_all('div', {'data-testid': 'result-snippet'})
    for s in snippets:
        print(s.text)
    browser.close()
