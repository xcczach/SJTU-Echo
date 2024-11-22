from data_utils.scrapper import extract_links, extract_sub_urls, extract_content
import argparse
import os
import re


def get_output_json():
    json_path = input("Please input the path (**/*.json) to dump results: ")
    # if json_path does not end with .json, append .json to the path
    if not json_path.endswith(".json"):
        json_path += ".json"
    # if json_path does not exist, create the directory along with the file
    if not os.path.exists(json_path):
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as f:
            f.write("{}")
    return json_path


def get_output_dir():
    output_dir = input("Please input the path of the output directory: ")
    # if output_dir does not exist, create the directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def get_urls_from_file(file_path: str):
    with open(file_path, "r") as f:
        all_content = f.read()
    url_pattern = r'http[s]?://[^\s<>"]+'
    urls = re.findall(url_pattern, all_content)
    return list(set(urls))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-links", action="store_true")
    parser.add_argument("--extract-sub-urls", action="store_true")
    parser.add_argument("--extract-content", action="store_true")
    args = parser.parse_args()

    if args.extract_links:
        target_url = input("Please input the target URL (http(s)://...): ")
        depth = input("Please input the scrapping depth (defaults to 1): ")
        if not depth:
            depth = 1
        else:
            depth = int(depth)
        extract_links(target_url, get_output_json(), depth)
    if args.extract_sub_urls:
        target_url = input("Please input the target URL (http(s)://...): ")
        extract_sub_urls(target_url, get_output_dir())
    if args.extract_content:
        urls_file_path = input(
            "Please input the path to the file containing URLs (http(s)://...): "
        )
        urls = get_urls_from_file(urls_file_path)
        print(f"Extracting content from {len(urls)} URLs")
        extract_content(urls, get_output_json())
