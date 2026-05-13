import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import argparse
import logging
import os
import urllib.parse
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_domain_from_urban_api(district_name, state=""):
    try:
        base_url = "https://educationdata.urban.org/api/v1/school-districts/ccd/directory/2021/"
        params = {"lea_name": district_name}
        if state:
            params["state_location"] = state

        res = requests.get(base_url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            for result in results:
                 if "url" in result and result["url"]:
                     return result["url"]
    except Exception as e:
        pass
    return None

def get_official_domain(district_name, state=""):
    # Bing is much more reliable and doesn't block as aggressively as Google or DuckDuckGo
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    query = f'{district_name} {state} school district official website'
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and href.startswith('http') and 'bing' not in href and 'microsoft' not in href:
                domain = urllib.parse.urlparse(href).netloc.lower()
                if any(x in domain for x in ['wikipedia', 'facebook', 'nces', 'niche', 'publicschoolreview', 'usnews', 'mapquest', 'greatschools', 'schooldigger', 'hometownlocator', 'yahoo', 'yellowpages', 'privateschoolreview', 'texastribune', 'local.', 'city-data', 'zillow', 'realtor', 'google', 'twitter']):
                    continue
                return f"{urllib.parse.urlparse(href).scheme}://{domain}"
    except Exception as e:
        logging.warning(f"Bing search failed: {e}")

    query = f'{district_name} {state} school district official website'
    url = "https://lite.duckduckgo.com/lite/"

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]

    import random
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"q": query}
    try:
        session = requests.Session()
        res = session.post(url, headers=headers, data=data, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and href.startswith('http') and 'duckduckgo' not in href:
                    domain = urllib.parse.urlparse(href).netloc.lower()
                    if any(x in domain for x in ['wikipedia', 'facebook', 'nces', 'niche', 'publicschoolreview', 'usnews', 'mapquest', 'greatschools', 'schooldigger', 'hometownlocator', 'yahoo', 'bing', 'yellowpages', 'privateschoolreview', 'texastribune', 'local.', 'city-data', 'zillow', 'realtor', 'abbott.com']):
                        continue
                    return f"{urllib.parse.urlparse(href).scheme}://{domain}"
    except Exception as e:
        pass

    try:
        url = "https://html.duckduckgo.com/html/"
        res = requests.post(url, headers=headers, data=data, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href')
                if href and href.startswith('http') and 'duckduckgo' not in href:
                    domain = urllib.parse.urlparse(href).netloc.lower()
                    if any(x in domain for x in ['wikipedia', 'facebook', 'nces', 'niche', 'publicschoolreview', 'usnews', 'mapquest', 'greatschools', 'schooldigger', 'hometownlocator', 'yahoo', 'bing', 'yellowpages', 'privateschoolreview', 'texastribune', 'local.', 'city-data', 'abbott.com']):
                        continue
                    return f"{urllib.parse.urlparse(href).scheme}://{domain}"
    except Exception as e:
        pass

    api_url = get_domain_from_urban_api(district_name, state)
    if api_url:
        if not api_url.startswith('http'):
            api_url = 'https://' + api_url
        return api_url

    return None

def extract_contact_with_llm(text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"""
        Extract the Name, Title, and Email of EVERY person you can find who works in the "Food Service" or "Child Nutrition" department from the following website text.
        This includes Directors, Managers, Dietitians, Supervisors, Buyers, Coordinators, and standard staff (e.g. Cafeteria Staff, Cook, etc).
        If titles are not explicitly "Food Service", look for roles related to food, nutrition, cafeteria, meals, etc.
        Return it as a JSON object containing a list named 'contacts'.
        If you cannot find anyone, return an empty list for 'contacts'.
        Format: {{"contacts": [{{"Name": "...", "Title": "...", "Email": "..."}}]}}

        Text: {text[:25000]}
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

    domain = None
    for attempt in range(2):
        domain = get_official_domain(district_name, state)
        if domain:
            break
        time.sleep(2)

    if not domain:
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', district_name).lower()
        if "isd" in clean_name:
            domain = f"https://www.{clean_name}.org"
        elif "usd" in clean_name:
            domain = f"https://www.{clean_name}.org"
        else:
            domain = f"https://www.{clean_name}.org"
        logging.warning(f"Could not find domain via search. Guessing {domain}")

    logging.info(f"Found domain: {domain}")

    pages_to_crawl = []
    # Add root first
    pages_to_crawl.append(domain)

    for path in ['/staff', '/departments', '/food-service', '/dining', '/nutrition', '/child-nutrition', '/food-and-nutrition', '/food-service-department', '/apps/staff/', '/apps/departments/', '/departments/food-service']:
        pages_to_crawl.append(f"{domain}{path}")

    all_text = ""
    emails = set()

    try:
         for p in ['/staff', '/o/district/staff', '/departments', '/apps/staff/', '/apps/departments/', '']:
            url = f"{domain}{p}"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            # Look for contact information across the whole page, especially tables or list elements
            # A lot of staff directories don't have explicit 'staff' classes, so extract raw text.
            text = soup.get_text(separator='\n', strip=True)
            if len(text) > 5 and text not in all_text:
                 all_text += text + "\n\n"

            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            for e in found_emails:
                emails.add(e)
    except:
        pass

    # No need to hit the exact same urls again since the first block does it,
    # but we can try the ones that are left in pages_to_crawl

    for url in set(pages_to_crawl) - set([f"{domain}{p}" for p in ['/staff', '/o/district/staff', '/departments', '/apps/staff/', '/apps/departments/', '']]):
        logging.info(f"Crawling {url}...")
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                if text not in all_text:
                    all_text += text + "\n\n"

                found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                for e in found_emails:
                    emails.add(e)
        except Exception as e:
            pass

    if use_llm and os.environ.get("OPENAI_API_KEY") and all_text:
        contacts = extract_contact_with_llm(all_text)
        if contacts:
            return contacts

    fallback_contacts = []
    food_keywords = ['food service', 'child nutrition', 'cafeteria', 'nutrition', 'dietitian', 'cook', 'buyer']
    lines = all_text.split('\n')
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in food_keywords) and len(line) < 200:
            # We found a line with a keyword, now let's get a bigger chunk of text around it to find context
            context = " ".join(lines[max(0, i-5):min(len(lines), i+6)])
            nearby_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', context)

            # Since many websites do not list emails directly, we should still extract the person's name!
            email = nearby_emails[0] if nearby_emails else "Not Found"

            # Try to guess the name from nearby lines if the keyword line is just a title
            name_guess = line.strip()[:50]
            if len(name_guess) < 5 or "director" in name_guess.lower() or "manager" in name_guess.lower():
                # Let's see if the line before it looks like a name
                if i > 0 and 5 < len(lines[i-1].strip()) < 40:
                    name_guess = lines[i-1].strip()

            fallback_contacts.append({
                "Name": name_guess,
                "Title": "Food Service/Child Nutrition Contact",
                "Email": email
            })

    if not fallback_contacts and emails:
        for e in list(emails)[:3]:
            fallback_contacts.append({
                "Name": "Name not extracted",
                "Title": "Food Service/Child Nutrition Contact",
                "Email": e
            })

    unique_contacts = []
    seen_emails = set()
    seen_names = set()
    for c in fallback_contacts:
        key = c['Email'] + c['Name']
        if key not in seen_names:
            unique_contacts.append(c)
            seen_names.add(key)

    return unique_contacts

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
            for i, c in enumerate(contacts[:5]):
                district_info[f'Child Nutrition / Food Service Role {i+1} - Name'] = c.get('Name', 'Not Found')
                district_info[f'Child Nutrition / Food Service Role {i+1} - Title'] = c.get('Title', 'Not Found')
                district_info[f'Child Nutrition / Food Service Role {i+1} - Email'] = c.get('Email', 'Not Found')

            output_data.append(district_info)

        pd.DataFrame(output_data).to_csv(output_csv, index=False)
        logging.info(f"Saved progress for {district_name} to {output_csv}")

        time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape school district nutrition staff contacts.")
    parser.add_argument('-i', '--input', required=True, help="Input CSV file containing a 'District Name' column")
    parser.add_argument('-o', '--output', required=True, help="Output CSV file path")
    parser.add_argument('--use-llm', action='store_true', help="Use OpenAI API for better extraction (requires OPENAI_API_KEY env variable)")

    args = parser.parse_args()
    process_districts(args.input, args.output, args.use_llm)
