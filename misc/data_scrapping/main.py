DATA_DIR = "data"
from scrapper import StrSetDict, extract_links_recursively, clean_links_dict
from analyze import build_links_tree
import json
import argparse

LINKS_FILE_PATH = f"{DATA_DIR}/links.json"


def count_links(links_dict: StrSetDict) -> int:
    return sum(len(links) for links in links_dict.values())


def wrap_links_and_depth(links_dict: StrSetDict, depth: int) -> dict:
    return {"depth": depth, "links": links_dict}


def save_links(links_dict: StrSetDict, depth: int):
    links_dict = clean_links_dict(links_dict)
    with open(LINKS_FILE_PATH, "w") as f:
        json.dump(wrap_links_and_depth(links_dict, depth), f)
    print(f"{count_links(links_dict)} links saved to {LINKS_FILE_PATH}")


def load_links_and_depth() -> tuple[StrSetDict, int]:
    try:
        with open(LINKS_FILE_PATH, "r") as f:
            data = json.load(f)
        return data["links"], data["depth"]
    except:
        print(f"Failed to load links from {LINKS_FILE_PATH}, starting from scratch")
        return dict(), 1


def get_depth(links_dict: StrSetDict, start_url: str) -> int:
    depth = 0
    for url in links_dict:
        if start_url in links_dict[url]:
            depth += 1
    return depth


def extract_links():
    visited_links, _ = load_links_and_depth()
    extract_links_recursively(
        "https://www.sjtu.edu.cn/",
        max_depth=2,
        max_concurrency=10,
        wait_time=2,
        visited_links_dict=visited_links,
        recursion_callback=save_links,
    )
    visited_links, current_depth = load_links_and_depth()
    save_links(visited_links, current_depth)


def anaylze_links():
    links, _ = load_links_and_depth()
    root_url = "https://www.sjtu.edu.cn/"
    tree = build_links_tree(links, root_url)
    print(tree)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args()
    if args.extract:
        extract_links()
    if args.analyze:
        anaylze_links()


if __name__ == "__main__":
    main()
