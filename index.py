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
import requests



from workers.captcha import check_captcha_presence, solve_for_captcha, auto_captcha_solve
from workers.search_results import check_search_results
from workers.keywords import arr1, search_query
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




def get_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(executable_path="./cdriver/chromedriver", options=chrome_options)
    return driver
    
def search_google(driver, url):
    base_url = 'https://www.google.com/search?q='
    query = f'''inurl:{url} ({search_query})'''
    encoded_query = quote_plus(query)
    search_url = base_url + encoded_query
    driver.get(search_url)
    isCaptcha=check_captcha_presence(driver)
    if(isCaptcha):
        logging.error('Captcha Encountred')
        logging.info('Trying to auto solve captcha')
        solved=auto_captcha_solve(driver)
        if(not solved):
            logging.info("Can't auto solve captcha, please solve it manually to continue")
            solve_for_captcha(driver)
    hasKeywords = check_search_results(driver, url) 
    time.sleep(3)
    return hasKeywords

def read_excel_file(file_path, sheet_name):
    logging.info(f"Reading Excel file: {file_path}, sheet: {sheet_name}.")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        raise

def validate_columns(df, required_columns):
    logging.info("Validating columns in the Excel file.")
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"Missing columns in Excel file: {missing_columns}")
        raise ValueError(f"Missing columns: {missing_columns}")
    return df.astype(str)
    
def update_csv_with_links(file_path, sheet_name, output_csv_file):
    lead_sheet = read_excel_file(file_path, sheet_name)
    required_columns = ["Website URL"]
    lead_sheet = validate_columns(lead_sheet, required_columns)
    
    output_column1 = "Hose OR Cooling Hose OR IT Cooling Hose Keywords Found in site? (YES/NO)" 
    output_column1_links = "Cooling Hose Links"

    lead_sheet[output_column1] = ""
    lead_sheet = lead_sheet[lead_sheet["Website URL"].notna()]

    driver = get_driver()
    wait = WebDriverWait(driver, 10)
    total_rows = len(lead_sheet)
    
    with open(output_csv_file, mode='w', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["Website URL", output_column1,output_column1_links])
        csv_writer.writeheader()
        
        with tqdm(total=total_rows, file=sys.stdout, desc="Processing rows") as pbar:
            for index, row in lead_sheet.iterrows():
                try:
                    website_url = row["Website URL"]
                    keyword_check = search_google(driver, website_url) 
                    
                    row_data = {
                        "Website URL": website_url,
                        output_column1: 'NO',
                        
                       
                        output_column1_links: '',
                        
                    
                    }
                    

                    base_url = 'https://www.google.com/search?q='
                    query = f'''inurl:{website_url} ({search_query})'''
                    encoded_query = quote_plus(query)
                    search_url = base_url + encoded_query
                    row_data[output_column1_links] = search_url
                   
                   
                    
                    for keywordPair in keyword_check:
                        
                        if keywordPair[0] in arr1:
                            
                            row_data[output_column1] = 'YES'
                            row_data[output_column1_links] = keywordPair[1]
                       
                        
                    
                    csv_writer.writerow(row_data)
                    pbar.update(1)
                except Exception as e:
                    logging.error(f"Error processing row {index}: {e}")
                    pbar.update(1)
                    
    driver.quit()

if __name__ == "__main__":
    update_csv_with_links(
        file_path='./excel.xlsx',
        sheet_name='Sheet1',
        output_csv_file='./csvs/rawResults.csv'
    )