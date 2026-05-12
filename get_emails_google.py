from googlesearch import search
import requests
from bs4 import BeautifulSoup

def search_for_district(district_name):
    query = f'"{district_name}" food service directory OR staff email'
    for url in search(query, num_results=3, sleep_interval=2):
        print(url)
        try:
            # try to fetch the page
            res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text()
            import re
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            if emails:
                print("Found emails:", set(emails))
        except Exception as e:
            print("Failed to fetch", url)

search_for_district("Los Angeles Unified School District")
