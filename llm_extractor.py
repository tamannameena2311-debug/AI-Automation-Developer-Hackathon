from google import genai
from google.genai import types
import json
import os

def extract_company_info(text: str, api_key: str = None) -> dict:
    """Uses Gemini to extract structured JSON data from scraped text."""
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        
    if not api_key:
        raise ValueError("No API key provided. Set GEMINI_API_KEY environment variable or pass it directly.")
        
    client = genai.Client(api_key=api_key)
    
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
    """ + text

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
        # Ensure schema compliance and stability
        keys = ["website_name", "company_name", "address", "mobile_number", "mail", "core_service", "target_customer", "probable_pain_point", "outreach_opener"]
        for k in keys:
            if k not in data:
                if k == "mail":
                    data[k] = []
                else:
                    data[k] = ""
        return data
    except json.JSONDecodeError:
        print("Failed to parse JSON response from LLM.")
        # Return empty schema to not break app
        return {
            "website_name": "", "company_name": "", "address": "", 
            "mobile_number": "", "mail": [], "core_service": "", 
            "target_customer": "", "probable_pain_point": "", "outreach_opener": ""
        }
