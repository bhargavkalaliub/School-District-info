from googlesearch import search
from urllib.parse import urlparse

def get_domain(district_name):
    query = f'"{district_name}" official site'
    try:
        # Just grab the top 2 results
        for url in search(query, num_results=2):
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            if "wikipedia" not in domain and "facebook" not in domain and "linkedin" not in domain:
                return domain
    except Exception as e:
        return None
    return None

print(get_domain("Los Angeles Unified School District"))
print(get_domain("Chicago Public Schools"))
print(get_domain("Miami-Dade County Public Schools"))
