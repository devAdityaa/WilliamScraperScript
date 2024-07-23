import requests
import time
from bs4 import BeautifulSoup
from workers.keywords import keywords
def check_search_results(driver, matchUrl):
    try:
        # Wait until the search results are present
        results = driver.find_elements('css selector', 'div#rso>div>div')
        items = {}
        for i in range(min(8, len(results))):
            link = results[i].find_element('css selector', 'a[href]')
            item_url = link.get_attribute('href')
            resObj = check_website_text(item_url, matchUrl, items) # Pass an empty dict to accumulate results
            if(resObj==-1):
                resObj= use_selenium_to_get_text(driver,item_url, matchUrl, items)
            items.update(resObj)  # Merge the dictionaries
        return items if items else {}
        
    except Exception as e:
        return {}
def use_selenium_to_get_text(driver,url, matchUrl,obj):
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Get the text of the page
        text = driver.execute_script('return document.body.innerText')
        time.sleep(3)
        # Navigate back to the start page
        driver.back()
        
        # Check for keywords in the text
        for keyword in keywords:
            if keyword.lower() in text.lower():
                if keyword not in obj:
                    if url.startswith(matchUrl):
                        obj[keyword] = url
                        
        return obj
        
    except Exception as e:
        return {}
def check_website_text(url, matchUrl, obj):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get inner text
        text = soup.get_text(separator=' ', strip=True).lower()
        for keyword in keywords:
            if keyword.lower() in text:
                if keyword not in obj:
                    if url.startswith(matchUrl):
                        obj[keyword] = url
        return obj
    except requests.RequestException as e:
        return -1
