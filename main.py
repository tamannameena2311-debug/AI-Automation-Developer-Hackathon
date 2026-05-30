from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import uvicorn
import os

from scraper import smart_scrape
from llm_extractor import extract_company_info

app = FastAPI(title="AI & Automation Hackathon - Prospect Research")

class EnrichRequest(BaseModel):
    url: str

class CompanyProfile(BaseModel):
    website_name: str
    company_name: str
    address: str
    mobile_number: str
    mail: List[str]
    core_service: str
    target_customer: str
    probable_pain_point: str
    outreach_opener: str

# In-memory store for the hackathon
results_db = []

@app.post("/enrich", response_model=CompanyProfile)
async def enrich_company_endpoint(req: EnrichRequest):
    try:
        # 1. Scrape text
        scraped_text = smart_scrape(req.url)
        if not scraped_text:
            raise HTTPException(status_code=400, detail="Could not scrape text from URL. The site might be blocking crawlers or is inaccessible.")
            
        # 2. Extract with LLM
        data = extract_company_info(scraped_text)
        if not data:
             raise HTTPException(status_code=500, detail="Failed to extract structured data from LLM.")
             
        # 3. Save & Return
        results_db.append(data)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results", response_model=List[CompanyProfile])
async def get_results():
    return results_db

# Mount static files for the frontend UI
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
