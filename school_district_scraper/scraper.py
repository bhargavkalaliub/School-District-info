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
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_official_domain(district_name):
    query = f'"{district_name}" official website'
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
        Extract the Name, Title, and Email of the person related to "Food Service" or "Child Nutrition" from the following website text.
        If you find multiple, return the highest ranking one (Director, Manager, etc).
        If you cannot find the information, reply with 'Not Found' for that field.
        Format your response exactly as JSON: {{"Name": "...", "Title": "...", "Email": "..."}}

        Text: {text[:8000]}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )

        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"LLM Extraction failed: {e}")
        return {"Name": "Not Found", "Title": "Not Found", "Email": "Not Found"}

def crawl_for_nutrition_contact(district_name, use_llm=False):
    logging.info(f"Looking up domain for {district_name}...")
    domain = get_official_domain(district_name)

    if not domain:
        return "Not Found", "Not Found", "Not Found (No website found)"

    logging.info(f"Found domain: {domain}")

    # We will search google for the specific nutrition page on that domain
    query = f'site:{urllib.parse.urlparse(domain).netloc} "food service" OR "child nutrition" directory OR staff email'

    try:
        page_urls = list(search(query, num_results=2))
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
        extracted = extract_contact_with_llm(all_text)
        name = extracted.get("Name", "Not Found")
        title = extracted.get("Title", "Not Found")
        email = extracted.get("Email", "Not Found")

        # Fallback to regex emails if LLM misses it
        if email == "Not Found" and emails:
            email = list(emails)[0]

        return name, title, email

    if emails:
        return "Name not extracted", "Food Service/Child Nutrition Contact", list(emails)[0]

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

    for index, row in df.iterrows():
        district_name = row['District Name']
        logging.info(f"Processing District: {district_name}")

        name, title, email = crawl_for_nutrition_contact(district_name, use_llm)

        district_info = {
            'District Name': district_name,
            'Child Nutrition / Food Service - Name': name,
            'Child Nutrition / Food Service - Title': title,
            'Child Nutrition / Food Service - Email': email
        }

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
