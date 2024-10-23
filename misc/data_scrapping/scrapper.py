# Target Websites
# - https://www.sjtu.edu.cn/
# Searching Method
# Recursively search all the links in the website.
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 开启无头模式
    chrome_options.add_argument("--disable-gpu")  # 如果系统是Windows，防止出现一些bug
    chrome_options.add_argument("--no-sandbox")  # Linux下可能需要
    chrome_options.add_argument("--disable-dev-shm-usage")  # 为了避免资源受限的问题

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def close_driver(driver: WebDriver):
    driver.quit()

def href_to_absolute(url: str, href: str):
    return urljoin(url, href)

# Extract all the links in the website; return a set of links in absolute path.
def extract_links(driver: WebDriver, url: str, wait_time: float = 2.0):
    driver.get(url)
    time.sleep(wait_time)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set(a['href'] for a in soup.find_all('a', href=True))
    return links



if __name__ == "__main__":
    driver = get_driver()
    url = "https://www.sjtu.edu.cn/"
    print(f"Extracting links from {url}")
    links = extract_links(driver, url)
    print(links)
    close_driver(driver)