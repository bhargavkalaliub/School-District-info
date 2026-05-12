# School District Nutrition Staff Scraper

This is a Python-based tool designed to automate the process of searching for specific contact information (Name, Title, and Email) for nutrition and food service roles across various school districts.

Since there are over 13,000 public school districts in the US, running this manually for every district at once would take an extensive amount of time and likely result in search engine rate limiting. This script provides an automated approach using DuckDuckGo Search and optionally uses OpenAI's API to extract Names and Titles accurately from search snippets.

## Features

- Reads a list of target school districts from an input CSV file.
- Searches for specific roles using customized queries.
- Uses basic Regex to find emails.
- **Optional (Recommended):** Uses OpenAI's LLM to accurately parse unstructured search snippets and extract the exact Name, Title, and Email.
- Exports results progressively to an output CSV file, marking missing fields as "Not Found".

## Prerequisites

1. Python 3.8+ installed on your system.
2. An OpenAI API Key (optional, but highly recommended for accurate parsing).

## Installation

1. Navigate to this directory in your terminal.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

*(Note: Depending on your environment, you may need to use `pip3` instead of `pip`)*

## Input File Format

Create an input CSV file (e.g., `input_districts.csv`) with at least one column titled **exactly**: `District Name`.

Example `input_districts.csv`:
```csv
District Name
Los Angeles Unified School District
Chicago Public Schools
Miami-Dade County Public Schools
```

## Usage

### Basic Mode (Regex Email Extraction Only)
This mode only extracts emails and cannot reliably determine the staff member's exact name from search snippets.

```bash
python scraper.py -i input_districts.csv -o output_results.csv
```

### Advanced Mode (LLM Extraction - Recommended)
This mode uses OpenAI's GPT models to analyze the search results and reliably extract Name, Title, and Email.

1. Set your OpenAI API key as an environment variable:
   - **Mac/Linux:** `export OPENAI_API_KEY="your-api-key-here"`
   - **Windows CMD:** `set OPENAI_API_KEY="your-api-key-here"`
   - **Windows PowerShell:** `$env:OPENAI_API_KEY="your-api-key-here"`

2. Run the script with the `--use-llm` flag:

```bash
python scraper.py -i input_districts.csv -o output_results.csv --use-llm
```

## Note on Rate Limits
Search engines may block or rate-limit your IP address if you search too aggressively. The script includes an artificial delay (`time.sleep(2)`) between role searches. If you plan to process thousands of districts, you may need to run the script in batches or configure proxy servers.
