import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def duckduckgo_html_search(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        results = []
        for result in soup.find_all('div', class_='result__body'):
            title_elem = result.find('h2', class_='result__title')
            snippet_elem = result.find('a', class_='result__snippet')
            url_elem = result.find('a', class_='result__url')

            if title_elem and snippet_elem and url_elem:
                title = title_elem.get_text(strip=True)
                snippet = snippet_elem.get_text(strip=True)
                href = url_elem.get('href')

                # duckduckgo urls are wrapped in a redirect
                if "uddg=" in href:
                    href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])

                results.append({"title": title, "body": snippet, "href": href})

        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

res = duckduckgo_html_search('"Los Angeles Unified School District" "Food Service Director" email')
for r in res[:2]:
    print(r)
