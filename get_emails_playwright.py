from playwright.sync_api import sync_playwright
import re
import urllib.parse
from bs4 import BeautifulSoup

def search_bing_with_playwright(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        encoded_query = urllib.parse.quote_plus(query)
        page.goto(f'https://www.bing.com/search?q={encoded_query}')

        try:
            page.wait_for_selector('.b_algo', timeout=5000)
        except:
            pass

        content = page.content()
        browser.close()

        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ')

        # Extract emails
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))

        print("Text snippet:", text[:500])
        return [e for e in emails if "bing" not in e and "microsoft" not in e and "w3.org" not in e]

try:
    print(search_bing_with_playwright('"Los Angeles Unified School District" "Food Service Director" email'))
except Exception as e:
    print(e)
