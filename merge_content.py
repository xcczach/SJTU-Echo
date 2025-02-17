import json
import argparse

def merge_content_jsons(json_paths):
    merged_content = []
    for json_path in json_paths:
        with open(json_path, "r") as f:
            content = json.load(f)
            merged_content.extend(content)
    return merged_content

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-paths", type=str, nargs="+", required=True)
    parser.add_argument("--output-path", type=str, required=True)
    args = parser.parse_args()

    merged_content = merge_content_jsons(args.json_paths)
    with open(args.output_path, "w") as f:
        json.dump(merged_content, f)