import pandas as pd
import logging
import sys
import csv
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import quote_plus
import time
from bs4 import BeautifulSoup
import requests
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# Define keywords to check
keywords = [
    "Quick connector",
    "quick disconnect",
    "change connector",
    "fluid connector",
    "hydraulic connector",
    "connector"
]


def check_captcha_presence(driver):
    try:
        driver.find_element('css selector','#recaptcha')
        return 1
    except:
        return 0
def solve_for_captcha(driver):
    captcha = check_captcha_presence(driver)
    while(captcha):
        captcha = check_captcha_presence(driver)
        time.sleep(10)
    recheck = check_captcha_presence(driver)
    if(recheck):
        solve_for_captcha(driver)
    return
def get_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver
def browse_initial_sites(session, headers):
    logging.info("Starting initial site browsing.")
    sites = ["https://www.google.com", "https://www.wikipedia.org", "https://www.github.com"]
    
    
    for site in sites:
        try:
            response = session.get(site, headers=headers)
            response.raise_for_status()
            logging.info(f"Browsed site: {site}")
        except requests.RequestException as e:
            logging.error(f"Error browsing site {site}: {e}")

def search_google(driver, url, wait):
    # Base URL for Google search
    base_url = 'https://www.google.com/search?q='
    query = f'''inurl:{url} ("quick change connector" OR "connector" OR "quick disconnect connector" OR "quick connector" OR "fluid connector" OR "hydraulic connector" or "hydraulic" or "fluid") (product OR buy OR shop OR store OR price OR catalog OR 
            specifications)'''
    # Encode the query to be URL-safe
    encoded_query = quote_plus(query)
    
    # Construct the full URL
    search_url = base_url + encoded_query
    
    # Open the search URL
    driver.get(search_url)
    isCaptcha=check_captcha_presence(driver)
    
    if(isCaptcha):
        logging.error('Captcha Encountred, please solve capthca to continue')
        solve_for_captcha(driver)
    hasKeywords = check_search_results(driver, url)
    time.sleep(3)
    return hasKeywords

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
        logging.error(f"No Search Results {e}")
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
        logging.error(f"Error fetching URL {url}: {e}")
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
        logging.error(f"Error fetching URL {url}: {e}")
        return -1

def read_excel_file(file_path, sheet_name):
    logging.info(f"Reading Excel file: {file_path}, sheet: {sheet_name}.")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        logging.info(f"Excel file read successfully. Columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        raise

def validate_columns(df, required_columns):
    logging.info("Validating columns in the Excel file.")
    logging.info(f"Columns found in the file: {df.columns.tolist()}")
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"Missing columns in Excel file: {missing_columns}")
        raise ValueError(f"Missing columns: {missing_columns}")
    return df.astype(str)



    
def update_excel_with_products(file_path, sheet_name, output_csv_file):
    lead_sheet = read_excel_file(file_path, sheet_name)
    required_columns = ["Website URL"]
    lead_sheet = validate_columns(lead_sheet, required_columns)
    
    output_column1 = "Quick Change Connectors or Disconnect Connectors or Change Connectors Found in site? (YES/NO)"
    output_column2 = "Fluid Connectors or Hydraulic Connectors or Fluid or Hydraulic Found in site? (YES/NO)"
    output_column1_links = "Quick Change Connector Links"
    output_column2_links = "Fluid Connectors Links"

    lead_sheet[output_column1] = ""
    lead_sheet[output_column2] = ""

    # Filter only non-empty rows in the "Website URL" column
    lead_sheet = lead_sheet[lead_sheet["Website URL"].notna()]

    driver = get_driver()
    browse_initial_sites(session, headers)
    wait = WebDriverWait(driver, 10)
    total_rows = len(lead_sheet)
    
    # Open the CSV file for writing
    with open(output_csv_file, mode='w', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["Website URL", output_column1, output_column2, output_column1_links, output_column2_links])
        csv_writer.writeheader()
        
        with tqdm(total=total_rows, file=sys.stdout, desc="Processing rows") as pbar:
            for index, row in lead_sheet.iterrows():
                try:
                    website_url = row["Website URL"]
                    keyword_check = search_google(driver, "https://www." + website_url, wait)
                    print(keyword_check)
                    
                    arr1 = ['quick connector', 'quick disconnect', 'connector', "change connector"]
                    arr2 = ['fluid connector', 'hydraulic connector']
                    
                    row_data = {
                        "Website URL": website_url,
                        output_column1: 'NO',
                        output_column2: 'NO',
                        output_column1_links: '',
                        output_column2_links: ''
                    }
                    
                    if len(keyword_check) == 0:
                        base_url = 'https://www.google.com/search?q='
                        query = f'''inurl:{website_url} ("quick change connector" OR "connector" OR "quick disconnect connector" OR "quick connector" OR "fluid connector" OR "hydraulic connector" or "hydraulic" or "fluid") (product OR buy OR shop OR store OR price OR catalog OR specifications)'''
                        encoded_query = quote_plus(query)
                        search_url = base_url + encoded_query
                        row_data[output_column1_links] = search_url
                        row_data[output_column2_links] = search_url
                    else:
                        for keyword in keyword_check:
                            if keyword in arr1:
                                print("Arr1", keyword, keyword_check[keyword])
                                row_data[output_column1] = 'YES'
                                row_data[output_column1_links] = keyword_check[keyword]
                            elif keyword in arr2:
                                print("Arr2", keyword, keyword_check[keyword])
                                row_data[output_column2] = 'YES'
                                row_data[output_column2_links] = keyword_check[keyword]
                    
                    csv_writer.writerow(row_data)
                    pbar.update(1)
                except Exception as e:
                    logging.error(f"Error processing row {index}: {e}")
                    pbar.update(1)
                    
    driver.quit()

if __name__ == "__main__":
    update_excel_with_products(
        file_path='./excel.xlsx',
        sheet_name='Sheet1',
        output_csv_file='output.csv'
    )