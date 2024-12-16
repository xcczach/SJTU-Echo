#!/bin/bash

# 定义目标URL数组
target_urls=(
    "https://www.ji.sjtu.edu.cn/cn/"
    # 如果有更多的URL，可以在这里继续添加
    # "https://example.com/another-site"
)

# 定义对应的JSON路径数组
json_paths=(
    "database/raw/content/sjtu-ji.json"
    # 如果有更多的JSON路径，确保与URL数量对应
    # "database/raw/content/another-site.json"
)

# 输出目录
output_dir="database/raw"

# 检查两个数组的长度是否相同
if [ "${#target_urls[@]}" -ne "${#json_paths[@]}" ]; then
    echo "Error: The lengths of target_urls and json_paths arrays do not match."
    exit 1
fi

# 遍历数组中的每个元素
for index in "${!target_urls[@]}"; do
    url="${target_urls[$index]}"
    json_path="${json_paths[$index]}"

    echo "Starting processing URL: $url"
    echo "Output JSON path: $json_path"

    # 重复执行5次
    for run in {1..5}; do
        echo "Executing command run number $run..."
        python data_scrapper.py --extract-site --debug --target-url "$url" --output-dir "$output_dir" --json-path "$json_path"

        # 检查命令是否成功执行
        if [ $? -ne 0 ]; then
            echo "Command failed on run number $run. Continuing to the next command."
            break
        fi
    done

    echo "Finished processing URL: $url"
    echo "-----------------------------"
done

echo "All tasks completed."
