from data_scrapper import get_urls_from_file, get_output_json
import argparse
import json

def filter_links(file_path: str, link_prefixes: list[str]):
    links:list[str] = get_urls_from_file(file_path)
    result = []
    for link in links:
        for prefix in link_prefixes:
            if link.startswith(prefix):
                result.append(link)
                break
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter links from a file')
    parser.add_argument('--file-path', type=str, help='The path of the file')
    parser.add_argument('--link-prefixes', type=str, nargs='+', help='The prefixes of the links')
    parser.add_argument('--output-path', type=str, help='The path of the output file')
    args = parser.parse_args()

    file_path = args.file_path
    link_prefixes = args.link_prefixes
    output_path = args.output_path

    result = filter_links(file_path, link_prefixes)
    output_json_path = get_output_json(output_path)
    result_json = {"links": result}
    with open(output_json_path, 'w') as f:
        json.dump(result_json, f)
    print(f"{len(result)} links are filtered and saved to {output_json_path}")