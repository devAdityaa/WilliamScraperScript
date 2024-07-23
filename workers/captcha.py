import time

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