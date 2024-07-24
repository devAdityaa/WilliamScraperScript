import time
from selenium_recaptcha_solver import RecaptchaSolver

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
def auto_captcha_solve(driver):
    try:
        driver.delete_all_cookies()
        solver = RecaptchaSolver(driver=driver)
        captcha_iframe = driver.find_element('css selector','iframe[title="reCAPTCHA"]')
        solver.click_recaptcha_v2(iframe=captcha_iframe)
        return 1
    except:
        return 0