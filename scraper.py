import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re

def clean_html(html_content: str) -> str:
    """Removes boilerplate from HTML and returns clean text."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove script, style, header, footer, nav elements
    for element in soup(["script", "style", "header", "footer", "nav", "noscript"]):
        element.extract()
        
    text = soup.get_text(separator=" ", strip=True)
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)
    return text

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
    
    # Find links for About, Contact, Services
    links_to_visit = set()
    keywords = ["about", "contact", "service"]
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text().lower()
        
        # Check if link text or href contains our keywords
        if any(kw in text or kw in href.lower() for kw in keywords):
            full_url = urljoin(base_url, href)
            # Ensure we stay on the same domain
            if full_url.startswith(base_url) or full_url.startswith(base_url.replace("https://", "http://")):
                links_to_visit.add(full_url)
                
            if len(links_to_visit) >= 3: # Limit to 3 additional pages to save tokens
                break
                
    for link in links_to_visit:
        try:
            time.sleep(1) # Be polite
            res = requests.get(link, headers=headers, timeout=10)
            if res.status_code == 200:
                page_name = link.split("/")[-1] or "PAGE"
                scraped_text += f"\n=== {page_name.upper()} ===\n" + clean_html(res.text) + "\n"
        except Exception:
            continue
            
    # Truncate text if it's exceptionally large to avoid massive token usage
    max_chars = 25000 
    if len(scraped_text) > max_chars:
        scraped_text = scraped_text[:max_chars]
        
    return scraped_text

if __name__ == "__main__":
    print(smart_scrape("https://example.com"))
