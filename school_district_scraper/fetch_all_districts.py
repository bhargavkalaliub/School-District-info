import requests
import json
import csv
import logging

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
                state = district.get("state_location") # Get the state to improve search accuracy
                agency_type = district.get("agency_type", 0)
                if name and state and agency_type in [1, 2, 3]:
                    if "Department of Education" not in name:
                        districts.add((name, state))

            url = data.get("next")

            if len(districts) % 1000 < 50 and len(districts) > 0:
                logging.info(f"Loaded {len(districts)} districts...")

        logging.info(f"Successfully retrieved {len(districts)} unique school districts. Writing to {output_csv}...")

        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["District Name", "State"])
            for district_tuple in sorted(list(districts)):
                writer.writerow([district_tuple[0], district_tuple[1]])

        logging.info("Complete.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_all_school_districts("input_districts.csv")
