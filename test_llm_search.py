import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = """
What is the official domain name (just the domain, e.g., 'lausd.org' or 'cps.edu') for the following school districts?
Return the response as a valid JSON object mapping district names to their domain names:
1. Los Angeles Unified School District
2. Chicago Public Schools
3. Miami-Dade County Public Schools
"""

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    response_format={ "type": "json_object" }
)

print(response.choices[0].message.content)
