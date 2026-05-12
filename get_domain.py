import requests

def get_domain(district_name):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(district_name)}&utf8=&format=json"
    res = requests.get(url, headers=headers).json()
    if not res.get('query', {}).get('search'): return None
    pageid = res['query']['search'][0]['pageid']

    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extlinks&pageids={pageid}&format=json"
    res = requests.get(url, headers=headers).json()
    links = res.get('query', {}).get('pages', {}).get(str(pageid), {}).get('extlinks', [])
    for link in links:
        url = link['*']
        if "google" not in url and "archive" not in url:
            return url
    return None

print(get_domain("Los Angeles Unified School District"))
print(get_domain("Chicago Public Schools"))
print(get_domain("Miami-Dade County Public Schools"))
