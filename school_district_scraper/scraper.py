import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import argparse
from duckduckgo_search import DDGS
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

ROLES = [
    "Director of Child Nutrition / Food Service Director",
    "Director of Nutrition Services / Assistant Director",
    "Dietitian / Registered Dietitian",
    "Menu Planner / SNS (School Nutrition Specialist)",
    "Nutrition Specialist / Procurement Specialist",
    "Buyer / Coordinator",
    "Field Supervisor / Supervisor",
    "Cafeteria Manager / Area Manager",
    "Production Manager"
]

def extract_contact_with_llm(snippet, role):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"""
        Extract the Name, Title, and Email for the role roughly matching '{role}' from the following search snippet.
        If you cannot find the information, reply with 'Not Found' for that field.
        Format your response exactly as JSON: {{"Name": "...", "Title": "...", "Email": "..."}}

        Snippet: {snippet}
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )

        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"LLM Extraction failed: {e}")
        return {"Name": "Not Found", "Title": "Not Found", "Email": "Not Found"}

def search_role_for_district(district_name, role, ddgs, use_llm=False):
    """
    Use DuckDuckGo to search for the role in the district.
    We try a very specific targeted search first.
    """
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

    if not results:
        return "Not Found", "Not Found", "Not Found"

    combined_snippet = " ".join([res.get('body', '') + ' ' + res.get('title', '') for res in results])

    if use_llm and os.environ.get("OPENAI_API_KEY"):
        extracted = extract_contact_with_llm(combined_snippet, role)
        return extracted.get("Name", "Not Found"), extracted.get("Title", "Not Found"), extracted.get("Email", "Not Found")
    else:
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_regex, combined_snippet)
        if emails:
            # We found an email, but extracting the exact name without LLM is hard
            return "Name in snippet (requires manual review)", role, emails[0]

    return "Not Found", "Not Found", "Not Found"

def process_districts(input_csv, output_csv, use_llm=False):
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        logging.error(f"Failed to read {input_csv}: {e}")
        return

    if 'District Name' not in df.columns:
        logging.error("Input CSV must contain a column named 'District Name'.")
        return

    output_data = []

    with DDGS() as ddgs:
        for index, row in df.iterrows():
            district_name = row['District Name']
            logging.info(f"Processing District: {district_name}")

            district_info = {'District Name': district_name}

            for role in ROLES:
                name, found_title, email = search_role_for_district(district_name, role, ddgs, use_llm)

                # To avoid hitting rate limits too quickly
                time.sleep(2)

                role_key = role.split('/')[0].strip()
                district_info[f"{role_key} - Name"] = name
                district_info[f"{role_key} - Title"] = found_title
                district_info[f"{role_key} - Email"] = email

            output_data.append(district_info)

            # Save progress incrementally
            pd.DataFrame(output_data).to_csv(output_csv, index=False)
            logging.info(f"Saved progress for {district_name} to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape school district nutrition staff contacts.")
    parser.add_argument('-i', '--input', required=True, help="Input CSV file containing a 'District Name' column")
    parser.add_argument('-o', '--output', required=True, help="Output CSV file path")
    parser.add_argument('--use-llm', action='store_true', help="Use OpenAI API for better name/title extraction (requires OPENAI_API_KEY env variable)")

    args = parser.parse_args()
    process_districts(args.input, args.output, args.use_llm)
