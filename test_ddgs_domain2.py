from ddgs import DDGS
import json

with DDGS() as ddgs:
    res1 = list(ddgs.text("Los Angeles Unified School District official website", max_results=3))
    print(json.dumps(res1, indent=2))
