import requests
import time
from bs4 import BeautifulSoup
from workers.keywords import keywords
from urllib.parse import urlparse
def check_search_results(driver, matchUrl):
    try:
        # Wait until the search results are present
        results = driver.find_elements('css selector', 'div#rso>div>div')
        items = []
        for i in range(min(10, len(results))):
            link = results[i].find_element('css selector', 'a[href]')
            item_url = link.get_attribute('href')
            parsed_url = urlparse(item_url)
            domain = parsed_url.netloc
            if (matchUrl in domain) and not (item_url.lower().endswith('.pdf')):
                keywordsPresent = check_website_text(item_url) # Pass an empty dict to accumulate results

                if(type(keywordsPresent)==type(-1) or len(keywordsPresent)==0):
                    keywordsPresent= use_selenium_to_get_text(driver,item_url)
                if(len(keywordsPresent)):
                    items.extend(keywordsPresent)
            
        return items
        
    except Exception as e:
        return []
def use_selenium_to_get_text(driver,url):
    try:
        # Navigate to the URL
        driver.get(url)
        keywordsPresent = []
        # Get the text of the page
        text = driver.execute_script('return document.body.innerText')
        
        time.sleep(3)
        # Navigate back to the start page
        driver.back()
        if(text):
        # Check for keywords in the text
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    keywordsPresent.append([keyword,url])
                        
        return keywordsPresent
        
    except Exception as e:
        return []
def check_website_text(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        keywordsPresent = []
        # Get inner text
        text = soup.get_text(separator=' ', strip=True).lower()
        if(text):
            for keyword in keywords:
                if keyword.lower() in text:
                    keywordsPresent.append([keyword,url])
        return keywordsPresent
    except requests.RequestException as e:
        return -1
