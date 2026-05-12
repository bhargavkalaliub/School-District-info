FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Keep the container alive or run the default command
CMD ["python", "scraper.py", "-i", "input_districts.csv", "-o", "output_results.csv"]
