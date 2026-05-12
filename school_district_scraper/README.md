# School District Nutrition Staff Scraper

This is a Python-based tool designed to automate the process of searching for contact information (Name, Title, and Email) for nutrition and food service roles across various school districts.

**IMPORTANT NOTE ON RATE LIMITS:**
Because there are over 13,000 public school districts in the US, running this script on the entire list at once will result in your IP address being temporarily banned by Google (`429 Too Many Requests`). You **must** run this in smaller batches (e.g., 50-100 districts at a time) or use rotating residential proxies if you intend to scrape the entire country.

## How It Works (The Direct Domain Method)
Unlike standard web scrapers that just look at search engine snippets, this tool:
1. Searches Google for the official website domain of the School District.
2. Performs a targeted `site:domain.com` search to find the specific Food Service or Child Nutrition directory page.
3. Visits that page directly and extracts raw emails.
4. Uses OpenAI's LLM to read the webpage text and extract the exact Name, Title, and Email of the director.

## Prerequisites

1. Python 3.8+ installed on your system.
2. An OpenAI API Key (optional, but highly recommended for accurate parsing).

## Installation & Setup

You can run this tool natively on your machine, via Docker, or directly in GitHub Actions.

### Method 1: Local Python Environment
1. Navigate to this directory in your terminal.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

*(Note: Depending on your environment, you may need to use `pip3` instead of `pip`)*

### Method 2: Docker / Docker Compose
If you have Docker installed, you don't need to configure Python locally.
1. Place your `input_districts.csv` file in this directory.
2. If using the LLM mode (recommended), ensure your `.env` file exists or export `OPENAI_API_KEY` to your environment.
3. Run:
```bash
docker-compose up
```

### Method 3: GitHub Actions
If you host this repository on GitHub, you can run the scraper directly from the cloud:
1. Ensure `input_districts.csv` is committed to the repository inside the `school_district_scraper/` folder.
2. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> Add a New Repository Secret named `OPENAI_API_KEY`.
3. Go to the **Actions** tab in GitHub.
4. Select the **Run School District Scraper** workflow.
5. Click **Run workflow**. Once completed, the `output_results.csv` will be available as an Artifact download on the workflow run page.

## Input File Format

Create an input CSV file (e.g., `input_districts.csv`) with at least one column titled **exactly**: `District Name`.

*Note: You can generate a comprehensive list of all ~13,500 public school districts in the United States by running the included `fetch_all_districts.py` script. This script pulls the latest directory directly from the National Center for Education Statistics (NCES) API and outputs it to `input_districts.csv`.*

```bash
python fetch_all_districts.py
```

## Usage

Run the script:

```bash
python scraper.py -i input_districts.csv -o output_results.csv --use-llm
```
