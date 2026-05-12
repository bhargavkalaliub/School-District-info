import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import argparse
import logging
import os
import urllib.parse
from googlesearch import search

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_official_domain(district_name, state=""):
    query = f'"{district_name}" {state} official website'
    try:
        urls = list(search(query, num_results=2, sleep_interval=2))
        for url in urls:
            if "wikipedia" not in url and "facebook" not in url and "nces" not in url and "niche.com" not in url and "publicschoolreview" not in url:
                parsed = urllib.parse.urlparse(url)
                return f"{parsed.scheme}://{parsed.netloc}"
    except Exception as e:
        logging.error(f"Search failed for domain: {e}")
    return None

def extract_contact_with_llm(text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"""
        Extract the Name, Title, and Email of EVERY person you can find who works in the "Food Service" or "Child Nutrition" department from the following website text.
        This includes Directors, Managers, Dietitians, Supervisors, Buyers, Coordinators, and standard staff.
        Return it as a JSON object containing a list named 'contacts'.
        If you cannot find anyone, return an empty list for 'contacts'.
        Format: {{"contacts": [{{"Name": "...", "Title": "...", "Email": "..."}}]}}

        Text: {text[:8000]}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )

        import json
        return json.loads(response.choices[0].message.content).get('contacts', [])
    except Exception as e:
        logging.error(f"LLM Extraction failed: {e}")
        return []

def crawl_for_nutrition_contact(district_name, state="", use_llm=False):
    logging.info(f"Looking up domain for {district_name} ({state})...")
    domain = get_official_domain(district_name, state)

    if not domain:
        return []

    logging.info(f"Found domain: {domain}")

    # We will search google for the specific nutrition page on that domain
    query = f'site:{urllib.parse.urlparse(domain).netloc} "food service" OR "child nutrition" directory OR staff email'

    try:
        page_urls = list(search(query, num_results=2, sleep_interval=2))
        if not page_urls:
            page_urls = [domain] # fallback to homepage
    except:
        page_urls = [domain]

    all_text = ""
    emails = set()

    for url in page_urls:
        logging.info(f"Crawling {url}...")
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            all_text += text + "\n"

            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            for e in found_emails:
                emails.add(e)
        except Exception as e:
            logging.error(f"Failed to crawl {url}: {e}")

    if use_llm and os.environ.get("OPENAI_API_KEY") and all_text:
        contacts = extract_contact_with_llm(all_text)
        if contacts:
            return contacts


    fallback_contacts = []
    if emails:
        for e in list(emails)[:3]: # limit to 3 to prevent huge rows
            fallback_contacts.append({
                "Name": "Name not extracted",
                "Title": "Food Service/Child Nutrition Contact",
                "Email": e
            })
    return fallback_contacts

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

    for index, row in df.iterrows():
        district_name = row['District Name']
        state = row.get('State', '')
        logging.info(f"Processing District: {district_name} {state}")

        contacts = crawl_for_nutrition_contact(district_name, state, use_llm)

        if not contacts:
             district_info = {
                'District Name': district_name,
                'State': state,
                'Child Nutrition / Food Service Role 1 - Name': 'Not Found',
                'Child Nutrition / Food Service Role 1 - Title': 'Not Found',
                'Child Nutrition / Food Service Role 1 - Email': 'Not Found'
             }
             output_data.append(district_info)
        else:
            district_info = {
                'District Name': district_name,
                'State': state
            }
            # Add up to 5 contacts found
            for i, c in enumerate(contacts[:5]):
                district_info[f'Child Nutrition / Food Service Role {i+1} - Name'] = c.get('Name', 'Not Found')
                district_info[f'Child Nutrition / Food Service Role {i+1} - Title'] = c.get('Title', 'Not Found')
                district_info[f'Child Nutrition / Food Service Role {i+1} - Email'] = c.get('Email', 'Not Found')

            output_data.append(district_info)

        pd.DataFrame(output_data).to_csv(output_csv, index=False)
        logging.info(f"Saved progress for {district_name} to {output_csv}")

        time.sleep(2) # Prevent rate limiting

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape school district nutrition staff contacts.")
    parser.add_argument('-i', '--input', required=True, help="Input CSV file containing a 'District Name' column")
    parser.add_argument('-o', '--output', required=True, help="Output CSV file path")
    parser.add_argument('--use-llm', action='store_true', help="Use OpenAI API for better extraction (requires OPENAI_API_KEY env variable)")

    args = parser.parse_args()
    process_districts(args.input, args.output, args.use_llm)
