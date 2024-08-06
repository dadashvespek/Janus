import requests
from bs4 import BeautifulSoup
import json
from anth_sup import text_processor
import templates

def extract_json_to_dict(text):
    start_index = text.find('```json')
    if start_index == -1:
        return None
    
    end_index = text.find('```', start_index + 7)
    if end_index == -1:
        return None
    
    before_text = text[:start_index].strip()
    after_text = text[end_index + 3:].strip()
    
    json_string = text[start_index + 7:end_index].strip()
    
    try:
        json_data = json.loads(json_string)
        
        combined_text = (before_text + " " + after_text).strip()
        if len(combined_text) >= 5:
            json_data['surrounding_text'] = combined_text
        else:
            json_data['surrounding_text'] = None
        
        return json_data
    except json.JSONDecodeError:
        return None

def check_confidence(text, high_threshold=60, low_threshold=40):
    data = extract_json_to_dict(text)
    if data is None or 'confidence' not in data:
        return None, None
    
    confidence = data['confidence']
    surrounding_text = data.get('surrounding_text')
    
    if confidence >= high_threshold:
        return 1, surrounding_text
    elif confidence < low_threshold:
        return 0, surrounding_text
    else:
        return None, surrounding_text
def scrape_text(url, max_chars=200):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        if any(js in text for js in ("Javascript", "JavaScript")):
            return None
        return text[:max_chars] if len(text) > 10 else None
    
    except Exception as e:
        return None
    

def determine_with_llm(url, raw_url):
    text_of_scraped_url = scrape_text(raw_url)
    print(f"URL:{url}")
    print(text_of_scraped_url)
    prompt =f"You will be given a url and you need to respond with a confidence rating based on this sentence “Is this a URL related to healthcare revenue cycle work?” a confidence rating of 100 means its for sure related, and a confidence rating of 0 means its for sure unrelated, alongside a category. If you're not sure about the category, just leave it as Unknown, you will always need to respond with your answers wrapped in ```json ``` and in the following template: \n{templates.url_confidence}\n write a very brief text (not more than 10 words) of the reason behind the choice (eg:'URL had `health` in domain.'): {url} "
    if text_of_scraped_url:
        prompt +=f"\nHere is a short sample text scraped from the site to add additional context (it may or may not be be useful, ignore it if its not useful): `{text_of_scraped_url}`"
    print(prompt)
    response = text_processor(prompt)
    print(response)
    result = check_confidence(response)
    return result







if __name__ == '__main__':
    url = "https://www.bcbstx.com/provider/standards/standards-requirements/mppc"
    print(scrape_text(url))