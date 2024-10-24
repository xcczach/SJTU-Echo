# Target Websites
# - https://www.sjtu.edu.cn/
# Searching Method
# Recursively search all the links in the website.
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from bs4 import BeautifulSoup
import time
import asyncio
import math
from typing import Callable, TypeAlias, Awaitable
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin


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
    return links


# Extract all the links in the website; return a set of links in absolute path.
def extract_links(driver: WebDriver, url: str, wait_time: float = 2.0):
    driver.get(url)
    time.sleep(wait_time)
    links = _extract_links_from_source(driver.page_source)
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
    extract_function: Callable[
        [str, float], Awaitable[list[str]]
    ] = extract_links_async,
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
            links = await extract_function(start_url, wait_time)
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
                        extract_function,
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
            extract_links_async,
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
        text = element.text
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


def _normalize_url(url):
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    if (scheme == "http" and parsed.port == 80) or (
        scheme == "https" and parsed.port == 443
    ):
        netloc = parsed.hostname

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query = parsed.query
    if query:
        query_params = sorted(parse_qsl(query, keep_blank_values=True))
        query = urlencode(query_params)

    fragment = ""

    normalized = urlunparse((scheme, netloc, path, "", query, fragment))
    return normalized


def _urls_are_equal(url1, url2):
    """
    比较两个URL是否相同。
    """
    return _normalize_url(url1) == _normalize_url(url2)


async def _extract_target_url_from_dynamic_element_async(
    element: dict[str, str],
    base_url: str,
    sema: asyncio.Semaphore,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
    null_result="",
) -> str:
    async with sema:
        driver = get_driver()
        driver.get(base_url)
        await asyncio.sleep(base_wait_time)
        tag_name = element["tag"]
        try:
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
        except Exception as e:
            print(f"Error when extracting target url: {e}")
            close_driver(driver)
            return null_result
        if _urls_are_equal(result, base_url):
            result = null_result
        close_driver(driver)
        print(f"Extracted target url: {result}")
        return result


def get_base_url(url: str) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


# TODO: deal with page number in single page apps like https://www.seiee.sjtu.edu.cn/xzzx_bszn_yjs.html
# Extract all sub-urls in the website; return a set of sub-urls in absolute path; sub-urls starts with the base url.
# Sub-urls are from <a href="...">, <a href="javascript:;"> and clickable page number elements.
async def _extract_sub_urls_async(
    url: str,
    sema: asyncio.Semaphore,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
):
    base_url = get_base_url(url)
    driver = get_driver()
    driver.get(url)
    await asyncio.sleep(base_wait_time)
    source = driver.page_source
    dynamic_elements = await asyncio.to_thread(
        _extract_switch_page_elements_from_source, source
    )

    async def extract_links_from_dynamic_elements(elements):
        tasks = []
        null_result = ""
        for element in elements:
            task = asyncio.create_task(
                _extract_target_url_from_dynamic_element_async(
                    element, url, sema, base_wait_time, target_wait_time, null_result
                )
            )
            tasks.append(task)
        result = await asyncio.gather(*tasks)
        result = [link for link in result if link != null_result]
        return result

    dynamic_links = await extract_links_from_dynamic_elements(dynamic_elements)
    static_links = await asyncio.to_thread(_extract_links_from_source, source)
    static_links = [href_to_absolute(url, href) for href in static_links]
    js_elements = _extract_js_elements_from_links(static_links)
    js_links = await extract_links_from_dynamic_elements(js_elements)
    close_driver(driver)
    result = dynamic_links + js_links + static_links
    result = [link for link in result if link.startswith(base_url)]
    return result


def extract_sub_urls_recursively(
    start_url: str,
    max_depth: int = math.inf,
    max_concurrency: int = 3,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
    visited_links_dict: StrSetDict = dict(),
    current_depth=1,
    recursion_callback: Callable[[StrSetDict, int], None] | None = None,
):
    sema = asyncio.Semaphore(max_concurrency)
    visited = set()
    file_write_lock = asyncio.Lock()

    async def extract_function(start_url: str, wait_time: float = 2.0):
        return await _extract_sub_urls_async(
            start_url, sema, wait_time, target_wait_time
        )

    return asyncio.run(
        _extract_links_recursively_helper(
            start_url,
            sema,
            max_depth,
            base_wait_time,
            recursion_callback,
            extract_function,
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

    # start_url = "https://www.sjtu.edu.cn/"
    # result = extract_links_recursively(start_url, max_depth=2)
    # for url, links in result.items():
    #     print(f"Links length in {url}:")
    #     print(len(links))
    #     print()

    sema = asyncio.Semaphore(3)
    url = "https://www.seiee.sjtu.edu.cn/xzzx_bszn_yjs.html"
    result = asyncio.run(_extract_sub_urls_async(url, sema))
    print(result)
