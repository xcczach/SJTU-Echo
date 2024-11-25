from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import time
import asyncio
import math
from typing import Callable, TypeAlias, Awaitable
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
import aiohttp
from readability import Document
from datetime import datetime, timezone
import json
import os
import sys
from selenium.webdriver.firefox.service import Service


def _get_driver():
    options = Options()
    options.add_argument("--headless")
    prefs = {
        "download.default_directory": "",
        "download.prompt_for_download": False,
        "download_restrictions": 3,
        "profile.default_content_setting_values.automatic_downloads": 2,  # 阻止自动下载
    }
    options.add_experimental_option("prefs", prefs)
    if sys.platform == "win32":
        driver = webdriver.Chrome(options=options)
    elif sys.platform == "linux":
        service = Service(executable_path="/usr/local/bin/geckodriver")
        driver = webdriver.Firefox(service=service)
    else:
        raise Exception("Unsupported platform")
    return driver


def _close_driver(driver: WebDriver):
    driver.quit()


def href_to_absolute(url: str, href: str):
    return urljoin(url, href)


def _extract_links_from_source(source: str):
    soup = BeautifulSoup(source, "html.parser")
    links = set(a["href"] for a in soup.find_all("a", href=True))
    return links


# Extract all the links in the website; return a set of links in absolute path.
def _extract_links(driver: WebDriver, url: str, wait_time: float = 2.0):
    driver.get(url)
    time.sleep(wait_time)
    links = _extract_links_from_source(driver.page_source)
    links = [href_to_absolute(url, href) for href in links]
    return links


async def _extract_links_async(
    start_url: str,
    sema: asyncio.Semaphore,
    wait_time: float = 2.0,
):
    async with sema:
        driver = _get_driver()
        links = await asyncio.to_thread(_extract_links, driver, start_url, wait_time)
        _close_driver(driver)
        return links


StrSetDict: TypeAlias = dict[str, list[str]]


async def _extract_links_recursively_helper(
    start_url: str,
    max_depth: int = math.inf,
    wait_time: float = 2.0,
    recursion_callback: Callable[[StrSetDict, int], None] | None = None,
    extract_function: Callable[
        [str, float], Awaitable[list[str]]
    ] = _extract_links_async,
    link_filter: Callable[[str], bool] | None = None,
    _visited=set(),
    _depth=1,
    _result_dict: StrSetDict = dict(),
    _file_write_lock: asyncio.Lock = asyncio.Lock(),
):
    if start_url in _visited or _depth > max_depth:
        return
    _visited.add(start_url)
    if start_url not in _result_dict:
        links = await extract_function(start_url, wait_time)
        links = [_normalize_url(link) for link in links]
        _result_dict[start_url] = links
        if recursion_callback is not None:
            async with _file_write_lock:
                recursion_callback(_result_dict, _depth)
    else:
        links = _result_dict[start_url]
    tasks = []
    for link in links:
        if link not in _visited and (link_filter is None or link_filter(link)):
            task = asyncio.create_task(
                _extract_links_recursively_helper(
                    link,
                    max_depth,
                    wait_time,
                    recursion_callback,
                    extract_function,
                    link_filter,
                    _visited,
                    _depth + 1,
                    _result_dict,
                    _file_write_lock,
                )
            )
            tasks.append(task)
    await asyncio.gather(*tasks)


def _extract_links_recursively(
    start_url: str,
    max_depth: int = math.inf,
    max_concurrency: int = 3,
    wait_time: float = 2.0,
    visited_links_dict: StrSetDict = dict(),
    current_depth=1,
    recursion_callback: Callable[[StrSetDict, int], None] | None = None,
    link_filter: Callable[[str], bool] | None = None,
):
    start_url = _normalize_url(start_url)
    sema = asyncio.Semaphore(max_concurrency)
    visited = set()
    file_write_lock = asyncio.Lock()

    async def extract_function(start_url: str, wait_time: float = 2.0):
        return await _extract_links_async(start_url, sema, wait_time)

    return asyncio.run(
        _extract_links_recursively_helper(
            start_url,
            max_depth,
            wait_time,
            recursion_callback,
            extract_function,
            link_filter,
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
        driver = _get_driver()
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
            _close_driver(driver)
            return null_result
        if _urls_are_equal(result, base_url):
            result = null_result
        _close_driver(driver)
        return result


def _get_base_url(url: str) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


file_suffixes = None


def _is_file_url(url: str) -> bool:
    global file_suffixes
    if file_suffixes is None:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f"{script_dir}/config.json", "r") as f:
            config = json.load(f)
            file_suffixes = config["file_suffixes"]
    suffix = url.split(".")[-1]
    return suffix in file_suffixes


# TODO: deal with page number in single page apps like https://www.seiee.sjtu.edu.cn/xzzx_bszn_yjs.html
# Extract all sub-urls in the website; return a set of sub-urls in absolute path; sub-urls starts with the base url.
# Sub-urls are from <a href="...">, <a href="javascript:;"> and clickable page number elements.
async def _extract_sub_urls_async(
    url: str,
    sema: asyncio.Semaphore,
    sub_sema: asyncio.Semaphore,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
):
    base_url = _get_base_url(url)
    if _is_file_url(url):
        return []
    async with sema:
        driver = _get_driver()
        driver.get(url)
        await asyncio.sleep(base_wait_time)
        source = driver.page_source
        dynamic_elements = await asyncio.to_thread(
            _extract_switch_page_elements_from_source, source
        )

        async def _extract_links_from_dynamic_elements(elements):
            tasks = []
            null_result = ""
            for element in elements:
                task = asyncio.create_task(
                    _extract_target_url_from_dynamic_element_async(
                        element,
                        url,
                        sub_sema,
                        base_wait_time,
                        target_wait_time,
                        null_result,
                    )
                )
                tasks.append(task)
            result = await asyncio.gather(*tasks)
            result = [link for link in result if link != null_result]
            return result

        dynamic_links = await _extract_links_from_dynamic_elements(dynamic_elements)
        static_links = await asyncio.to_thread(_extract_links_from_source, source)
        static_links = [href_to_absolute(url, href) for href in static_links]
        js_elements = _extract_js_elements_from_links(static_links)
        js_links = await _extract_links_from_dynamic_elements(js_elements)
        _close_driver(driver)
    result = dynamic_links + js_links + static_links
    result = [link for link in result if link.startswith(base_url)]
    return result


def _extract_sub_urls_recursively(
    start_url: str,
    max_depth: int = math.inf,
    max_concurrency: int = 3,
    max_sub_concurrency: int = 3,
    base_wait_time: float = 2.0,
    target_wait_time: float = 2.0,
    visited_links_dict: StrSetDict = dict(),
    current_depth=1,
    recursion_callback: Callable[[StrSetDict, int], None] | None = None,
    link_filter: Callable[[str], bool] | None = None,
):
    start_url = _normalize_url(start_url)
    sema = asyncio.Semaphore(max_concurrency)
    sub_sema = asyncio.Semaphore(max_sub_concurrency)
    visited = set()
    file_write_lock = asyncio.Lock()

    async def extract_function(start_url: str, wait_time: float = 2.0):
        return await _extract_sub_urls_async(
            start_url, sema, sub_sema, wait_time, target_wait_time
        )

    return asyncio.run(
        _extract_links_recursively_helper(
            start_url,
            max_depth,
            base_wait_time,
            recursion_callback,
            extract_function,
            link_filter,
            visited,
            current_depth,
            visited_links_dict,
            file_write_lock,
        )
    )


class HTMLContent:
    def __init__(self, url: str, content: dict, scraped_at: float):
        self.url = url
        self.content = content
        self.scraped_at = scraped_at

    def to_dict(self):
        return {
            "url": self.url,
            "content": self.content,
            "scraped_at": self.scraped_at,
        }


def _get_time_now():
    return datetime.now(timezone.utc).timestamp()


async def _fetch_content_static_async(url: str, session: aiohttp.ClientSession):
    if _is_file_url(url):
        print(f"_fetch_content_static_async: Skipping file URL: {url}")
        return ""
    async with session.get(url) as response:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or "text/html" in content_type:
            return await response.text()
        else:
            print(
                f"_fetch_content_static_async: Unsupported content type: {content_type}"
            )
            return ""


def _fetch_content_dynamic(url: str, max_wait_time: float = 10.0):
    if _is_file_url(url):
        print(f"_fetch_content_dynamic: Skipping file URL: {url}")
        return ""
    driver = _get_driver()
    driver.get(url)
    WebDriverWait(driver, max_wait_time).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    content = driver.page_source
    _close_driver(driver)
    return content


async def _fetch_content_dynamic_async(url: str, max_wait_time: float = 10.0):
    return await asyncio.to_thread(_fetch_content_dynamic, url, max_wait_time)


def _readability_process_content(content: str):
    try:
        doc = Document(content)
        doc_content = {
            "title": doc.title(),
            "body": doc.summary(),
        }
    except Exception as e:
        print(f"_readability_process_content: {e}")
        doc_content = {"title": "", "body": ""}
    return doc_content


def get_raw_content(content: str):
    return {
        "title": "",
        "body": content,
    }


async def _extract_content_static_async_helper(
    url: str,
    session: aiohttp.ClientSession,
    process_function: Callable[[str], dict] = _readability_process_content,
):
    content = await _fetch_content_static_async(url, session)
    doc_content = process_function(content)
    return HTMLContent(url, doc_content, _get_time_now())


async def _extract_content_static_async(
    url: str,
    session: aiohttp.ClientSession | None = None,
    process_function: Callable[[str], dict] = _readability_process_content,
):
    if session is None:
        async with aiohttp.ClientSession() as session:
            return await _extract_content_static_async_helper(
                url, session, process_function
            )
    return await _extract_content_static_async_helper(url, session)


async def _extract_content_dynamic_async(
    url: str,
    process_function: Callable[[str], dict] = _readability_process_content,
    max_wait_time: float = 10.0,
):
    content = await _fetch_content_dynamic_async(url, max_wait_time)
    doc_content = process_function(content)
    return HTMLContent(url, doc_content, _get_time_now())


def _load_links_and_depth(path: str) -> tuple[StrSetDict, int]:
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data["links"], data["depth"]
    except:
        return dict(), 1


def _wrap_links_and_depth(links_dict: StrSetDict, depth: int) -> dict:
    return {"depth": depth, "links": links_dict}


def _count_links(links_dict: StrSetDict) -> int:
    return sum(len(links) for links in links_dict.values())


def _save_links(links_dict: StrSetDict, depth: int, path: str):
    with open(path, "w") as f:
        json.dump(_wrap_links_and_depth(links_dict, depth), f)
    print(f"{_count_links(links_dict)} links saved to {path}")


# Remove circular references and duplicates; normalize urls
def _get_cleaned_links_dict(links_dict: StrSetDict, start_url: str):
    visited = set()
    cleaned_dict = dict()

    def visit(url):
        if url in links_dict:
            cleaned_dict[url] = list(set(links_dict[url]))
            cleaned_dict[url] = [
                child_url for child_url in cleaned_dict[url] if child_url not in visited
            ]
            if not cleaned_dict[url]:
                del cleaned_dict[url]
                return
            for child_url in cleaned_dict[url]:
                visited.add(child_url)
            for child_url in cleaned_dict[url]:
                visit(child_url)

    start_url = _normalize_url(start_url)
    visited.add(start_url)
    visit(start_url)

    return cleaned_dict


def _get_sub_urls_file_path(result_dir: str, url: str, cleaned: bool = False) -> str:
    sub_urls_dir = f"{result_dir}/sub_urls"
    if not os.path.exists(sub_urls_dir):
        os.makedirs(sub_urls_dir)
    return f"{sub_urls_dir}/{url.replace('://', '_').strip('/').replace('/', '_')}{'_raw' if not cleaned else ''}.json"


class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.value) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    @property
    def depth(self):
        if len(self.children) == 0:
            return 0
        return max(child.depth for child in self.children) + 1


def _build_links_tree(urls_dict: StrSetDict, root_url: str):
    root_url = _normalize_url(root_url)
    root = TreeNode(root_url)

    def add_children(node: TreeNode, url: str):
        if url in urls_dict:
            for child_url in urls_dict[url]:
                child_node = TreeNode(child_url)
                node.add_child(child_node)
                add_children(child_node, child_url)

    add_children(root, root_url)
    return root


def _get_depth(links_dict: StrSetDict, start_url: str) -> int:
    links_tree = _build_links_tree(links_dict, start_url)
    return links_tree.depth


def extract_links(root_url: str, result_path: str, max_depth: int = 2):
    """
    Extract all the links starting from root_url recursively; return a set of links in absolute path; links do not need to start with the base url.
    result_path: the path to save the extracted links, need to be .json.
    max_depth: the maximum depth of the recursion, suggested not larger than 2 to avoid too slow execution.
    """
    raw_result_path = result_path.replace(".json", "_raw.json")
    visited_links, _ = _load_links_and_depth(path=raw_result_path)
    _extract_links_recursively(
        root_url,
        max_depth=max_depth,
        max_concurrency=10,
        wait_time=2,
        visited_links_dict=visited_links,
        recursion_callback=lambda links_dict, depth: _save_links(
            links_dict, depth, path=raw_result_path
        ),
    )
    visited_links, current_depth = _load_links_and_depth(path=raw_result_path)
    _save_links(visited_links, current_depth, path=raw_result_path)
    visited_links = _get_cleaned_links_dict(visited_links, root_url)
    _save_links(visited_links, current_depth, path=result_path)


def extract_sub_urls(url: str, result_path: str):
    """
    Extract all sub-urls in the website starting from url recursively; save a set of sub-urls in absolute path to result_path; sub-urls starts with the base url.
    Sub-urls are from <a href="...">, <a href="javascript:;"> and clickable page number elements.
    result_path: the directory to save the extracted sub-urls.
    """

    def preclean_sub_urls(url: str):
        visited_links, _ = _load_links_and_depth(
            path=_get_sub_urls_file_path(result_path, url, cleaned=False)
        )
        visited_links = _get_cleaned_links_dict(visited_links, url)
        _save_links(
            visited_links,
            _get_depth(visited_links, url),
            path=_get_sub_urls_file_path(result_path, url, cleaned=True),
        )

    def link_filter(url: str):
        return not bool(re.search(r"/\d+\.html$", url))

    preclean_sub_urls(url)
    file_path = _get_sub_urls_file_path(result_path, url, cleaned=False)
    visited_links, _ = _load_links_and_depth(path=file_path)
    _extract_sub_urls_recursively(
        url,
        max_concurrency=3,
        max_sub_concurrency=5,
        base_wait_time=2,
        target_wait_time=2,
        visited_links_dict=visited_links,
        recursion_callback=lambda links_dict, depth: _save_links(
            links_dict, depth, path=file_path
        ),
        link_filter=link_filter,
    )
    visited_links, current_depth = _load_links_and_depth(path=file_path)
    visited_links = _get_cleaned_links_dict(visited_links, url)
    file_path = _get_sub_urls_file_path(url, cleaned=True)
    _save_links(visited_links, current_depth, path=file_path)


def _save_contents(contents: list[HTMLContent], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([content.to_dict() for content in contents], f, ensure_ascii=False)
    print(f"{len(contents)} contents saved to {path}")


def extract_content(urls: list[str], result_path: str):
    """
    Extract the content from each url in urls; save the results to result_path.
    result_path: the path to save the extracted contents, need to be .json.
    """

    async def extract_content_async(urls: list[str]):
        async with aiohttp.ClientSession() as session:
            tasks = [_extract_content_static_async(url, session) for url in urls]
            static_results = await asyncio.gather(*tasks)

        DYNAMIC_RESCRAP_THRESHOLD = 400
        dynamic_urls = [
            item.url
            for item in static_results
            if len(item.content["body"]) < DYNAMIC_RESCRAP_THRESHOLD
        ]
        static_results = [
            item for item in static_results if item.url not in dynamic_urls
        ]
        tasks = [
            _extract_content_dynamic_async(url, get_raw_content) for url in dynamic_urls
        ]
        dynamic_results = await asyncio.gather(*tasks)
        return static_results + dynamic_results

    results = asyncio.run(extract_content_async(urls))
    _save_contents(results, result_path)
