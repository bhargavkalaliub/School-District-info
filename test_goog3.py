from googlesearch import search
try:
    for url in search("Los Angeles Unified School District official website", num_results=3, sleep_interval=5):
        print(url)
except Exception as e:
    print(e)
