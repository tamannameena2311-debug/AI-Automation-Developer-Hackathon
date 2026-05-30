# ================================
# INSTALL DEPENDENCIES (Run this cell first in a new block)
# ================================
# !pip install beautifulsoup4 requests google-genai

# ================================
# 🏆 Hackathon Template Notebook
# Prospect Research Agent
# ================================
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re
import json
from google import genai
from google.genai import types

# ========= CONFIG =========
# 🔑 Add your API key here
API_KEY = "YOUR_API_KEY"

# ========= HELPER FUNCTIONS =========
def clean_html(html_content: str) -> str:
    """Removes boilerplate from HTML and returns clean text."""
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "header", "footer", "nav", "noscript"]):
        element.extract()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r'\s+', ' ', text)

def smart_scrape(base_url: str) -> str:
    """Scrapes the base url and heuristically finds Contact/About pages to scrape as well."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {base_url}: {e}")
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    scraped_text = "=== HOME PAGE ===\n" + clean_html(response.text) + "\n"
    
    links_to_visit = set()
    keywords = ["about", "contact", "service"]
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text().lower()
        if any(kw in text or kw in href.lower() for kw in keywords):
            full_url = urljoin(base_url, href)
            if full_url.startswith(base_url) or full_url.startswith(base_url.replace("https://", "http://")):
                links_to_visit.add(full_url)
            if len(links_to_visit) >= 3:
                break
                
    for link in links_to_visit:
        try:
            time.sleep(1)
            res = requests.get(link, headers=headers, timeout=10)
            if res.status_code == 200:
                page_name = link.split("/")[-1] or "PAGE"
                scraped_text += f"\n=== {page_name.upper()} ===\n" + clean_html(res.text) + "\n"
        except Exception:
            continue
            
    max_chars = 25000 
    if len(scraped_text) > max_chars:
        scraped_text = scraped_text[:max_chars]
        
    return scraped_text

# ========= REQUIRED FUNCTION =========
def enrich_company(url: str) -> dict:
    """
    Input: Company URL
    Output: Structured company profile (STRICT FORMAT)
    """
    if API_KEY == "YOUR_API_KEY":
        raise ValueError("Please set your Gemini API_KEY in the CONFIG block above.")
        
    scraped_text = smart_scrape(url)
    if not scraped_text:
        return {
            "website_name": "", "company_name": "", "address": "", 
            "mobile_number": "", "mail": [], "core_service": "", 
            "target_customer": "", "probable_pain_point": "", "outreach_opener": ""
        }

    client = genai.Client(api_key=API_KEY)
    
    prompt = """
    Extract the following information from the provided company text and return it strictly as a JSON object adhering to this exact schema:
    {
      "website_name": "String (Name of the website/company)",
      "company_name": "String (Official registered company name)",
      "address": "String (Full address, or empty string if not found)",
      "mobile_number": "String (Phone number, or empty string if not found)",
      "mail": ["Array of Strings (Emails found, empty array if none)"],
      "core_service": "String (Primary service or product they offer)",
      "target_customer": "String (Who their primary customers are)",
      "probable_pain_point": "String (A likely pain point their customers face that they solve)",
      "outreach_opener": "String (A short, personalized cold outreach intro based on their core service)"
    }
    
    CRITICAL RULES:
    1. If a field is missing or cannot be confidently determined, return an empty string "" or an empty array [] for lists. 
    2. Do NOT hallucinate data. If you don't see it in the text, leave it empty.
    3. Return ONLY valid JSON, without any markdown formatting or backticks.
    
    Company Text:
    """ + scraped_text

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        ),
    )
    
    try:
        data = json.loads(response.text)
        keys = ["website_name", "company_name", "address", "mobile_number", "mail", "core_service", "target_customer", "probable_pain_point", "outreach_opener"]
        for k in keys:
            if k not in data:
                if k == "mail": data[k] = []
                else: data[k] = ""
        return data
    except json.JSONDecodeError:
        return {
            "website_name": "", "company_name": "", "address": "", 
            "mobile_number": "", "mail": [], "core_service": "", 
            "target_customer": "", "probable_pain_point": "", "outreach_opener": ""
        }

# ============================================================================
# SECOND BOX - EXECUTED AT THE BOTTOM
# ============================================================================

# ========= 9. MAIN EXECUTION =========
if __name__ == "__main__":
    # 👉 Getting input dynamically
    import ast
    urls_input = input("Please paste your array of URLs (e.g. ['https://example.com']): ")
    
    try:
        urls = ast.literal_eval(urls_input)
    except:
        print("Invalid array format. Make sure it's a valid python list, e.g. ['url1', 'url2']")
        urls = []

    results = []

    for url in urls:
        print(f"Processing: {url} ...")
        try:
            data = enrich_company(url)
            results.append(data)
        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Save results to JSON file
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Results saved to results.json")

    # Print results for evaluation
    print("\n=== FINAL OUTPUT ===\n")
    print(json.dumps(results, indent=2))
