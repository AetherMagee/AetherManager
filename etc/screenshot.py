from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def makeScreenshot(targetSite, code):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("prefs", {"download.default_directory":"/dev/null"})
    driver = webdriver.Chrome('/bin/chromedriver', chrome_options=chrome_options)
    driver.get(targetSite)
    screenshot = driver.save_screenshot(f'temp/screenshot_{str(code)}.png')
    driver.quit()
