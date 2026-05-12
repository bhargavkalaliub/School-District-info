import requests
import json
import csv
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def fetch_all_school_districts(output_csv):
    base_url = "https://educationdata.urban.org/api/v1/school-districts/ccd/directory/2021/"
    districts = set()

    url = base_url

    logging.info(f"Fetching public school districts from the National Center for Education Statistics (NCES) database...")

    try:
        while url:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                logging.error(f"Failed to fetch data from {url}. Status Code: {response.status_code}")
                break

            data = response.json()
            results = data.get("results", [])

            for district in results:
                name = district.get("lea_name")
                # Agency Type 1 = Local school district that is not a component of a supervisory union.
                # Agency Type 2 = Local school district component of a supervisory union sharing a superintendent and administrative services with other local school districts.
                # Just filter out empty names or generic state agencies (agency_type >= 4 usually state/fed agencies, but 1 and 2 are normal public school districts)
                agency_type = district.get("agency_type", 0)
                if name and agency_type in [1, 2, 3]:
                    # Cleaning up names (e.g. "Albertville City" -> "Albertville City School District" if it doesn't have district in name, but we'll leave as is to be accurate)
                    # Exclude obvious non-districts
                    if "Department of Education" not in name:
                        districts.add(name)

            url = data.get("next")

            # Print progress
            if len(districts) % 1000 < 50 and len(districts) > 0:
                logging.info(f"Loaded {len(districts)} districts...")

        # Write to output CSV
        logging.info(f"Successfully retrieved {len(districts)} unique school districts. Writing to {output_csv}...")

        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["District Name"])
            for district in sorted(districts):
                writer.writerow([district])

        logging.info("Complete.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_all_school_districts("input_districts.csv")
