import requests
from bs4 import BeautifulSoup
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

response = requests.get('https://www.google.com/search?q="Los+Angeles+Unified+School+District"+"Director+of+Food+Services"+email', headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
for g in soup.find_all('div', class_='VwiC3b'):
    print(g.text)
