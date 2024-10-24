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
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def close_driver(driver: WebDriver):
    driver.quit()


def href_to_absolute(url: str, href: str):
    return urljoin(url, href)


def _extract_links_from_source(source: str):
    soup = BeautifulSoup(source, "html.parser")
    links = set(a["href"] for a in soup.find_all("a", href=True))
    links = [href_to_absolute(url, href) for href in links]
    return links


# Extract all the links in the website; return a set of links in absolute path.
def extract_links(driver: WebDriver, url: str, wait_time: float = 2.0):
    driver.get(url)
    time.sleep(wait_time)
    links = _extract_links_from_source(driver.page_source)
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
        else:
            links = _result_dict[start_url]
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
    visited = set()
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


def _extract_switch_page_elements_from_source(source: str) -> list[dict[str, str]]:
    numeric_elements = []
    soup = BeautifulSoup(source, "html.parser")
    for element in soup.find_all(string=True):
        text = element.strip()
        if re.fullmatch(r"\d+", text):
            parent_tag = element.parent
            numeric_elements.append(parent_tag)
    return [{"tag": element.name, "text": element.text} for element in numeric_elements]


def _extract_js_elements_from_links(links: list[str]) -> list[str]:
    js_links = []
    for link in links:
        if "javascript" in link:
            js_links.append(link)
    return [{"tag": "a", "href": link} for link in js_links]


async def _extract_target_url_from_dynamic_element_async(
    element: dict[str, str],
    base_url: str,
    sema: asyncio.Semaphore,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
) -> str:
    async with sema:
        driver = get_driver()
        driver.get(base_url)
        await asyncio.sleep(base_wait_time)
        tag_name = element["tag"]
        if "href" in element:
            href = element["href"]
            selenium_element = driver.find_element(
                By.XPATH, f"//{tag_name}[@href='{href}']"
            )
        else:
            text = element["text"]
            selenium_element = driver.find_element(
                By.XPATH, f"//{tag_name}[text()='{text}']"
            )
        actions = ActionChains(driver)
        actions.move_to_element(selenium_element).click().perform()
        await asyncio.sleep(target_wait_time)
        result = driver.current_url
        close_driver(driver)
        return result


# Extract all the links in the website; return a set of links in absolute path.
# Links are from <a href="...">, <a href="javascript:;"> and clickable page number elements.
async def _extract_sub_urls_async(
    url: str,
    sema: asyncio.Semaphore,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
):
    driver = get_driver()
    driver.get(url)
    await asyncio.sleep(base_wait_time)
    source = driver.page_source
    dynamic_elements = await asyncio.to_thread(
        _extract_switch_page_elements_from_source, source
    )

    async def extract_links_from_dynamic_elements(elements):
        tasks = []
        for element in elements:
            task = asyncio.create_task(
                _extract_target_url_from_dynamic_element_async(
                    element, url, sema, base_wait_time, target_wait_time
                )
            )
            tasks.append(task)
        return await asyncio.gather(*tasks)

    dynamic_links = await extract_links_from_dynamic_elements(dynamic_elements)
    static_links = await asyncio.to_thread(_extract_links_from_source, source)
    js_elements = _extract_js_elements_from_links(static_links)
    js_links = await extract_links_from_dynamic_elements(js_elements)
    close_driver(driver)
    return dynamic_links + js_links + static_links


if __name__ == "__main__":
    # driver = get_driver()
    # url = "https://www.sjtu.edu.cn/"
    # print(f"Extracting links from {url}")
    # links = extract_links(driver, url)
    # print(links)
    # close_driver(driver)

    # start_url = "https://www.sjtu.edu.cn/"
    # result = extract_links_recursively(start_url, max_depth=2)
    # for url, links in result.items():
    #     print(f"Links length in {url}:")
    #     print(len(links))
    #     print()

    sema = asyncio.Semaphore(3)
    url = "https://www.sjtu.edu.cn/tg/index.html"
    result = asyncio.run(_extract_sub_urls_async(url, sema))
    print(result)
