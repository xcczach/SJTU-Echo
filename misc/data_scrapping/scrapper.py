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
import asyncio
import math
from typing import Callable, TypeAlias


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")

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
    links = set(a["href"] for a in soup.find_all("a", href=True))
    links = [href_to_absolute(url, href) for href in links]
    return links


async def extract_links_async(start_url: str, wait_time: float = 2.0):
    driver = get_driver()
    links = await asyncio.to_thread(extract_links, driver, start_url, wait_time)
    close_driver(driver)
    return links


StrSetDict: TypeAlias = dict[str, list[str]]


async def _extract_links_recursively_helper(
    start_url: str,
    sema: asyncio.Semaphore,
    max_depth: int = math.inf,
    wait_time: float = 2.0,
    recursion_callback: Callable[[StrSetDict, int], None] | None = None,
    _visited=set(),
    _depth=1,
    _result_dict: StrSetDict = dict(),
    _file_write_lock: asyncio.Lock = asyncio.Lock(),
):
    if start_url in _visited or _depth > max_depth:
        return

    async with sema:
        _visited.add(start_url)
        if start_url not in _result_dict:
            links = await extract_links_async(start_url, wait_time)
            _result_dict[start_url] = links
            if recursion_callback is not None:
                async with _file_write_lock:
                    recursion_callback(_result_dict, _depth)
        tasks = []
        for link in links:
            if link not in _visited:
                task = asyncio.create_task(
                    _extract_links_recursively_helper(
                        link,
                        sema,
                        max_depth,
                        wait_time,
                        recursion_callback,
                        _visited,
                        _depth + 1,
                        _result_dict,
                        _file_write_lock,
                    )
                )
                tasks.append(task)
        await asyncio.gather(*tasks)
    return _result_dict


def extract_links_recursively(
    start_url: str,
    max_depth: int = math.inf,
    max_concurrency: int = 3,
    wait_time: float = 2.0,
    visited_links_dict: StrSetDict = dict(),
    current_depth=1,
    recursion_callback: Callable[[StrSetDict, int], None] | None = None,
):
    sema = asyncio.Semaphore(max_concurrency)
    visited = set(visited_links_dict.keys())
    file_write_lock = asyncio.Lock()
    return asyncio.run(
        _extract_links_recursively_helper(
            start_url,
            sema,
            max_depth,
            wait_time,
            recursion_callback,
            visited,
            current_depth,
            visited_links_dict,
            file_write_lock,
        )
    )


if __name__ == "__main__":
    # driver = get_driver()
    # url = "https://www.sjtu.edu.cn/"
    # print(f"Extracting links from {url}")
    # links = extract_links(driver, url)
    # print(links)
    # close_driver(driver)

    start_url = "https://www.sjtu.edu.cn/"
    result = extract_links_recursively(start_url, max_depth=2)
    for url, links in result.items():
        print(f"Links length in {url}:")
        print(len(links))
        print()
