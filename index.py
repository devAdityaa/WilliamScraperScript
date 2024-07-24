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
from workers.keywords import arr1, arr2, arr3, search_query
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
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
    
    output_column1 = "Quick Change Connectors or Disconnect Connectors or Change Connectors Found in site? (YES/NO)"
    output_column2 = "Fluid Connectors or Hydraulic Connectors or Fluid or Hydraulic Found in site? (YES/NO)"
    output_column3 = "Coupling (YES/NO)"
    output_column3_links = "Coupling Links"
    output_column1_links = "Quick Change Connector Links"
    output_column2_links = "Fluid Connectors Links"

    lead_sheet[output_column1] = ""
    lead_sheet[output_column2] = ""
    lead_sheet[output_column3] = ""
    lead_sheet = lead_sheet[lead_sheet["Website URL"].notna()]

    driver = get_driver()
    wait = WebDriverWait(driver, 10)
    total_rows = len(lead_sheet)
    
    with open(output_csv_file, mode='w', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["Website URL", output_column1, output_column2, output_column3, output_column1_links, output_column2_links, output_column3_links])
        csv_writer.writeheader()
        
        with tqdm(total=total_rows, file=sys.stdout, desc="Processing rows") as pbar:
            for index, row in lead_sheet.iterrows():
                try:
                    website_url = row["Website URL"]
                    keyword_check = search_google(driver, "https://www." + website_url)
                    print(keyword_check)
                    
                    
                    row_data = {
                        "Website URL": website_url,
                        output_column1: 'NO',
                        output_column2: 'NO',
                        output_column3: 'NO',
                        output_column1_links: '',
                        output_column2_links: '',
                        output_column3_links: ''
                    }
                    

                    base_url = 'https://www.google.com/search?q='
                    query = f'''inurl:{website_url} ("quick change connector" OR "connector" OR "quick disconnect connector" OR "quick connector" OR "fluid connector" OR "hydraulic connector" or "hydraulic" or "fluid") (product OR buy OR shop OR store OR price OR catalog OR specifications)'''
                    encoded_query = quote_plus(query)
                    search_url = base_url + encoded_query
                    row_data[output_column1_links] = search_url
                    row_data[output_column2_links] = search_url
                    row_data[output_column3_links] = search_url
                    
                    for keyword in keyword_check:
                        if keyword in arr1:
                            print("Arr1", keyword, keyword_check[keyword])
                            row_data[output_column1] = 'YES'
                            row_data[output_column1_links] = keyword_check[keyword]
                        elif keyword in arr2:
                            print("Arr2", keyword, keyword_check[keyword])
                            row_data[output_column2] = 'YES'
                            row_data[output_column2_links] = keyword_check[keyword]
                        elif keyword in arr3:
                            print("Arr2", keyword, keyword_check[keyword])
                            row_data[output_column3] = 'YES'
                            row_data[output_column3_links] = keyword_check[keyword]
                    
                    csv_writer.writerow(row_data)
                    pbar.update(1)
                except Exception as e:
                    logging.error(f"Error processing row {index}: {e}")
                    pbar.update(1)
                    
    driver.quit()

if __name__ == "__main__":
    update_csv_with_links(
        file_path='./excel.xlsx',
        sheet_name='Sheet3',
        output_csv_file='./csvs/example.csv'
    )