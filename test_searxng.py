import requests

url = "https://searx.be/search"
params = {
    "q": 'Los Angeles Unified School District "Director of Food Services" OR "Food Services Director" email',
    "format": "json"
}

response = requests.get(url, params=params)
if response.status_code == 200:
    for res in response.json().get('results', [])[:5]:
        print(res.get('title'))
        print(res.get('content'))
        print('---')
