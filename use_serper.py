import requests
import json
import os

url = "https://google.serper.dev/search"

payload = json.dumps({
  "q": "Los Angeles Unified School District Director of Child Nutrition OR Food Service Director email"
})
headers = {
  'X-API-KEY': os.environ.get("SERPER_API_KEY", ""),
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
