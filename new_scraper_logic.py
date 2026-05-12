import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
import re

def search_wikipedia_for_domain(district_name):
    # Search for district on Wikipedia to get the official website link
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(district_name)}&utf8=&format=json"
        res = requests.get(url, headers=headers).json()
        if not res.get('query', {}).get('search'): return None
        pageid = res['query']['search'][0]['pageid']

        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extlinks&pageids={pageid}&format=json"
        res = requests.get(url, headers=headers).json()
        links = res.get('query', {}).get('pages', {}).get(str(pageid), {}).get('extlinks', [])
        for link in links:
            href = link['*']
            if "google" not in href and "archive" not in href and "facebook" not in href:
                parsed = urllib.parse.urlparse(href)
                return parsed.netloc.replace('www.', '')
    except Exception as e:
        return None
    return None

def fetch_bing_page(query):
    # Headless scraping of Bing with requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text(separator=' ')
        return text
    except:
        return ""

district = "Los Angeles Unified School District"
domain = search_wikipedia_for_domain(district)
print("Found domain:", domain)

if domain:
    text = fetch_bing_page(f"site:{domain} food service director email")
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
    emails = [e for e in emails if "bing" not in e and "microsoft" not in e]
    print("Found emails via Bing:", emails)
