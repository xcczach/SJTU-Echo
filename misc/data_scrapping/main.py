DATA_DIR = "data"
from scrapper import (
    StrSetDict,
    extract_links_recursively,
    get_base_url,
    extract_sub_urls_recursively,
)
from analyze import (
    build_links_tree,
    get_cleaned_links_dict,
    get_kw_nodes,
)
import json
import argparse

RAW_LINKS_FILE_PATH = f"{DATA_DIR}/links_raw.json"
CLEANED_LINKS_FILE_PATH = f"{DATA_DIR}/links.json"
SUB_URLS_DIR = f"{DATA_DIR}/sub_urls"


def get_sub_urls_file_path(url: str, cleaned: bool = False) -> str:
    return f"{SUB_URLS_DIR}/{url.replace('://', '_').strip('/').replace('/', '_')}{'_raw' if not cleaned else ''}.json"


def count_links(links_dict: StrSetDict) -> int:
    return sum(len(links) for links in links_dict.values())


def wrap_links_and_depth(links_dict: StrSetDict, depth: int) -> dict:
    return {"depth": depth, "links": links_dict}


def save_links(links_dict: StrSetDict, depth: int, path: str = RAW_LINKS_FILE_PATH):
    with open(path, "w") as f:
        json.dump(wrap_links_and_depth(links_dict, depth), f)
    print(f"{count_links(links_dict)} links saved to {path}")


def load_links_and_depth(path: str = RAW_LINKS_FILE_PATH) -> tuple[StrSetDict, int]:
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data["links"], data["depth"]
    except:
        print(f"Failed to load links from {path}, starting from scratch")
        return dict(), 1


def get_depth(links_dict: StrSetDict, start_url: str) -> int:
    links_tree = build_links_tree(links_dict, start_url)
    return links_tree.depth


def extract_links():
    visited_links, _ = load_links_and_depth(path=RAW_LINKS_FILE_PATH)
    root_url = "https://www.sjtu.edu.cn/"
    extract_links_recursively(
        root_url,
        max_depth=2,
        max_concurrency=10,
        wait_time=2,
        visited_links_dict=visited_links,
        recursion_callback=save_links,
    )
    visited_links, current_depth = load_links_and_depth(path=RAW_LINKS_FILE_PATH)
    save_links(visited_links, current_depth, path=RAW_LINKS_FILE_PATH)
    visited_links = get_cleaned_links_dict(visited_links, root_url)
    save_links(visited_links, current_depth, path=CLEANED_LINKS_FILE_PATH)


def anaylze_links():
    links, _ = load_links_and_depth(path=CLEANED_LINKS_FILE_PATH)
    root_url = "https://www.sjtu.edu.cn/"
    tree = build_links_tree(links, root_url)
    kw = "sjtu"
    print(f"Searching for {kw} in the tree")
    kw_nodes = get_kw_nodes(tree, kw)
    print(f"Found {len(kw_nodes)} nodes containing {kw}")
    print(kw_nodes)
    print("Extracting base urls")
    base_urls = set([get_base_url(node.value) for node in kw_nodes])
    print(base_urls)


def preclean_sub_urls(url: str):
    visited_links, _ = load_links_and_depth(
        path=get_sub_urls_file_path(url, cleaned=False)
    )
    visited_links = get_cleaned_links_dict(visited_links, url)
    save_links(
        visited_links,
        get_depth(visited_links, url),
        path=get_sub_urls_file_path(url, cleaned=True),
    )


def extract_sub_urls(url: str):
    preclean_sub_urls(url)
    file_path = get_sub_urls_file_path(url, cleaned=False)
    visited_links, _ = load_links_and_depth(path=file_path)
    extract_sub_urls_recursively(
        url,
        max_concurrency=3,
        max_sub_concurrency=5,
        base_wait_time=2,
        target_wait_time=2,
        visited_links_dict=visited_links,
        recursion_callback=lambda links_dict, depth: save_links(
            links_dict, depth, path=file_path
        ),
    )
    visited_links, current_depth = load_links_and_depth(path=file_path)
    visited_links = get_cleaned_links_dict(visited_links, url)
    file_path = get_sub_urls_file_path(url, cleaned=True)
    save_links(visited_links, current_depth, path=file_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-links", action="store_true")
    parser.add_argument("--extract-sub-urls-from", type=str)
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args()
    if args.extract_links:
        extract_links()
    if args.analyze:
        anaylze_links()
    if args.extract_sub_urls_from:
        extract_sub_urls(args.extract_sub_urls_from)


if __name__ == "__main__":
    main()
