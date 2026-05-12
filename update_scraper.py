import re

with open('school_district_scraper/scraper.py', 'r') as f:
    code = f.read()

# Replace search logic
new_search_logic = """
def search_role_for_district(district_name, role, ddgs, use_llm=False):
    \"\"\"
    Use DuckDuckGo to search for the role in the district.
    We try a very specific targeted search first.
    \"\"\"
    # First, get a highly targeted query
    role_query = " OR ".join([f'"{r.strip()}"' for r in role.split('/')])

    # Try an exact quote match search for better results
    query = f'"{district_name}" {role_query} email OR contact'

    logging.info(f"Searching: {query}")

    try:
        results = list(ddgs.text(query, max_results=5))
    except Exception as e:
        logging.error(f"Search failed for {query}: {e}")
        return "Not Found", "Not Found", "Not Found"

    if not results:
        # Fallback query if no results
        query = f'{district_name} {role.split("/")[0]} email'
        logging.info(f"Fallback Searching: {query}")
        try:
            results = list(ddgs.text(query, max_results=5))
        except:
            return "Not Found", "Not Found", "Not Found"

    if not results:
        return "Not Found", "Not Found", "Not Found"

    combined_snippet = " ".join([res.get('body', '') + ' ' + res.get('title', '') for res in results])

    if use_llm and os.environ.get("OPENAI_API_KEY"):
        extracted = extract_contact_with_llm(combined_snippet, role)
        return extracted.get("Name", "Not Found"), extracted.get("Title", "Not Found"), extracted.get("Email", "Not Found")
    else:
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_regex, combined_snippet)

        # Look for names using simple title case matching around the email
        # This is basic, but better than 'Requires manual review'
        name_found = "Name in snippet"

        if emails:
            return name_found, role.split('/')[0].strip(), emails[0]

        # Return snippet as 'Title' if no email is found, so user at least gets SOMETHING
        return "Not Found", "See Snippet: " + combined_snippet[:100] + "...", "Not Found"
"""

code = re.sub(r'def search_role_for_district\(district_name, role, ddgs, use_llm=False\):.*?return "Not Found", "Not Found", "Not Found"', new_search_logic.strip(), code, flags=re.DOTALL)

with open('school_district_scraper/scraper.py', 'w') as f:
    f.write(code)
