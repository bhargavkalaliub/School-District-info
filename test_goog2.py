from googlesearch import search
for j in search('"Los Angeles Unified School District" "Director of Food Services" email', num_results=3, advanced=True):
    print(j.title)
    print(j.description)
