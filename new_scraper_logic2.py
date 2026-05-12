import os
import requests

def get_emails_with_llm(district, role):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"""
        I am compiling a directory of school district staff.
        What is the Name, Title, and Email of the {role} at {district}?
        If you know it based on your training data or can accurately infer the likely email pattern based on the district's domain (e.g., first.last@lausd.net), please provide it. If you don't know the person's name, return "Not Found".
        Format your response exactly as JSON: {{"Name": "...", "Title": "...", "Email": "..."}}
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
        return {"Name": "Not Found", "Title": "Not Found", "Email": "Not Found"}

print(get_emails_with_llm("Los Angeles Unified School District", "Director of Food Services"))
