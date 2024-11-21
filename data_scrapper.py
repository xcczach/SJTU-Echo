from data_utils.scrapper import extract_links, extract_sub_urls, extract_content
import argparse
import os

def get_output_json():
    json_path = input("Please input the path to dump results: ")
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-links", type=str, default=None)
    parser.add_argument("--extract-sub-urls", type=str, default=None)
    parser.add_argument("--extract-content", type=str, default=None)
    args = parser.parse_args()

    if args.extract_links:
        extract_links(args.extract_links, get_output_json())
    if args.extract_sub_urls:
        extract_sub_urls(args.extract_sub_urls, get_output_dir())
    if args.extract_content:
        extract_content(args.extract_content, get_output_json())