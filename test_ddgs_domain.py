from ddgs import DDGS
with DDGS() as ddgs:
    results = list(ddgs.text("site:lausd.org Director of Food Services email", max_results=5))
    for r in results: print(r)
