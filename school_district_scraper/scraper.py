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
        res = session.post(url, headers=headers, data=data, timeout=5)
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
        res = requests.post(url, headers=headers, data=data, timeout=5)
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
        import os
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f'''
        Extract the contact information for the following 9 specific roles within the "Food Service" or "Child Nutrition" department from the provided text.

        Roles to look for:
        1. Director of Child Nutrition / Food Service Director
        2. Director of Nutrition Services / Assistant Director
        3. Dietitian / Registered Dietitian
        4. Menu Planner / SNS (School Nutrition Specialist)
        5. Nutrition Specialist / Procurement Specialist
        6. Buyer / Coordinator
        7. Field Supervisor / Supervisor
        8. Cafeteria Manager / Area Manager
        9. Production Manager

        If you find a person that generally matches one of these roles, map them to the best fit.
        Return it as a JSON object containing a dictionary named 'contacts' where the keys are the exact role names listed above.
        For each role, provide a dictionary with "Name", "Title", and "Email".
        If a specific role is vacant or not listed in the text, set the "Name", "Title", and "Email" fields to "Not Found".

        Format:
        {{
          "contacts": {{
            "Director of Child Nutrition / Food Service Director": {{"Name": "...", "Title": "...", "Email": "..."}},
            "Director of Nutrition Services / Assistant Director": {{"Name": "...", "Title": "...", "Email": "..."}},
            ...
          }}
        }}

        Text: {text[:25000]}
        '''

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )

        import json
        return json.loads(response.choices[0].message.content).get('contacts', {})
    except Exception as e:
        import logging
        logging.error(f"LLM Extraction failed: {e}")
        return {}

def crawl_for_nutrition_contact(district_name, state="", website="", use_llm=False):
    logging.info(f"Looking up domain for {district_name} ({state})...")

    domain = None
    if pd.notna(website) and website and website != "None":
        domain = str(website)
        if not domain.startswith('http'):
            domain = 'https://' + domain
    else:
        for attempt in range(1):
            domain = get_official_domain(district_name, state)
            if domain:
                break

        if not domain:
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', district_name).lower()
            state_lower = state.lower() if state else "us"

            # Domains to try in order
            domains_to_try = [
                f"https://www.{clean_name}.org",
                f"https://www.{clean_name}.net",
                f"https://www.{clean_name}.com",
                f"https://www.{clean_name}.us",
                f"https://www.{clean_name}.k12.{state_lower}.us"
            ]

            # We will default to .org if all fail, but we'll try to find a valid one first
            domain = domains_to_try[0]
            for try_domain in domains_to_try:
                try:
                    res = requests.head(try_domain, timeout=2, headers={"User-Agent": "Mozilla/5.0"})
                    if res.status_code < 400:
                        domain = try_domain
                        break
                except:
                    continue
            logging.warning(f"Could not find domain via search. Guessing {domain}")

    logging.info(f"Found domain: {domain}")

    pages_to_crawl = []
    pages_to_crawl.append(domain)

    for path in [
        '/staff', '/departments', '/food-service', '/dining', '/nutrition',
        '/child-nutrition', '/food-and-nutrition', '/food-service-department',
        '/apps/staff/', '/apps/departments/', '/departments/food-service',
        '/staff-directory', '/administration', '/departments/child-nutrition'
    ]:
        pages_to_crawl.append(f"{domain}{path}")

    all_text = ""
    emails = set()

    # Homepage dynamic scraping
    try:
        res = requests.get(domain, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Scrape dynamically found nutrition links from homepage
        for a in soup.find_all('a'):
            href = a.get('href')
            text = a.get_text().lower()
            if href and ('food' in text or 'nutrition' in text or 'dining' in text):
                if href.startswith('/'):
                    href = domain + href
                if href.startswith('http') and domain in href:
                    pages_to_crawl.append(href)

        text = soup.get_text(separator='\n', strip=True)
        if len(text) > 5 and text not in all_text:
             all_text += text + "\n\n"
    except:
        pass

    # Specific CMS directory locations
    try:
         for p in ['/staff', '/o/district/staff', '/departments', '/apps/staff/', '/apps/departments/']:
            url = f"{domain}{p}"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            if len(text) > 5 and text not in all_text:
                 all_text += text + "\n\n"

            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            for e in found_emails:
                emails.add(e)
    except:
        pass

    seen_urls = set()
    unique_pages = []
    for p in pages_to_crawl:
        if p not in seen_urls:
            unique_pages.append(p)
            seen_urls.add(p)

    for url in unique_pages[:15]:
        logging.info(f"Crawling {url}...")
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')

                # Extract mailto links directly
                for a in soup.find_all('a', href=True):
                    if a['href'].startswith('mailto:'):
                        email_addr = a['href'][7:].split('?')[0].strip()
                        emails.add(email_addr)
                        # Also add a hint to the text so LLM can use it
                        name_hint = a.get_text().strip()
                        if name_hint and email_addr not in name_hint:
                            all_text += f"\nContact: {name_hint} Email: {email_addr}\n"

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
            context = " ".join(lines[max(0, i-5):min(len(lines), i+6)])
            nearby_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', context)

            email = nearby_emails[0] if nearby_emails else "Not Found"

            name_guess = line.strip()[:50]
            if len(name_guess) < 5 or "director" in name_guess.lower() or "manager" in name_guess.lower() or "staff" in name_guess.lower() or "services" in name_guess.lower() or "menu" in name_guess.lower() or "update" in name_guess.lower() or "department" in name_guess.lower() or "program" in name_guess.lower():
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

    # In fallback, try to build a dict structured like the LLM output
    unique_contacts_dict = {}

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

    # Initialize all with Not Found
    for role in ROLES:
        unique_contacts_dict[role] = {"Name": "Not Found", "Title": "Not Found", "Email": "Not Found"}

    seen_names = set()
    for c in fallback_contacts:
        if len(c['Name']) < 4 or len(c['Name']) > 40 or any(x in c['Name'].lower() for x in ['menu', 'update', 'department', 'program', 'service', 'nutrition']):
             continue
        key = c['Email'] + c['Name']
        if key not in seen_names:
            seen_names.add(key)
            # Just assign the first one found to Director as a fallback guess
            if unique_contacts_dict["Director of Child Nutrition / Food Service Director"]["Name"] == "Not Found":
                unique_contacts_dict["Director of Child Nutrition / Food Service Director"] = c

    return unique_contacts_dict

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
        website = row.get('Website', '')
        logging.info(f"Processing District: {district_name} {state}")

        contacts = crawl_for_nutrition_contact(district_name, state, website, use_llm)

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

        district_info = {
            'District Name': district_name,
            'State': state,
            'Website': website
        }

        if not contacts or not isinstance(contacts, dict):
            for role in ROLES:
                district_info[f'{role} - Name'] = 'Not Found'
                district_info[f'{role} - Title'] = 'Not Found'
                district_info[f'{role} - Email'] = 'Not Found'
        else:
            for role in ROLES:
                role_data = contacts.get(role, {})
                district_info[f'{role} - Name'] = role_data.get('Name', 'Not Found')
                district_info[f'{role} - Title'] = role_data.get('Title', 'Not Found')
                district_info[f'{role} - Email'] = role_data.get('Email', 'Not Found')

        output_data.append(district_info)

        pd.DataFrame(output_data).to_csv(output_csv, index=False)
        logging.info(f"Saved progress for {district_name} to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape school district nutrition staff contacts.")
    parser.add_argument('-i', '--input', required=True, help="Input CSV file containing a 'District Name' column")
    parser.add_argument('-o', '--output', required=True, help="Output CSV file path")
    parser.add_argument('--use-llm', action='store_true', help="Use OpenAI API for better extraction (requires OPENAI_API_KEY env variable)")

    args = parser.parse_args()
    process_districts(args.input, args.output, args.use_llm)
