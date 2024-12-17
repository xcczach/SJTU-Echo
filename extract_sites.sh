#!/bin/bash

# 定义目标URL数组
# Define the array of target URLs
target_urls=(
    "http://bwc.sjtu.edu.cn/"
    "http://www.shsmu.edu.cn/"
    "https://news.sjtu.edu.cn/"
    "http://www.gs.sjtu.edu.cn/"
    "https://www.lib.sjtu.edu.cn/"
    "http://www.seiee.sjtu.edu.cn/"
    "http://bme.sjtu.edu.cn/"
    "http://www.aero.sjtu.edu.cn/"
    "http://www.physics.sjtu.edu.cn/"
    "http://scce.sjtu.edu.cn/"
    "http://soo.sjtu.edu.cn/"
    "http://www.agri.sjtu.edu.cn/"
    "http://pharm.sjtu.edu.cn/"
    "http://law.sjtu.edu.cn/"
    "http://sfl.sjtu.edu.cn/"
    "http://shss.sjtu.edu.cn/"
    "http://www.sipa.sjtu.edu.cn/"
    "http://smc.sjtu.edu.cn/"
    "https://designschool.sjtu.edu.cn/"
    "http://www.saif.sjtu.edu.cn/"
    "http://speit.sjtu.edu.cn/"
    "https://www.ji.sjtu.edu.cn/cn/"
)

# 定义对应的JSON路径数组
# Define the corresponding JSON paths array
json_paths=(
    "database/raw/content/sjtu-bwc.json"
    "database/raw/content/sjtu-shsmu.json"
    "database/raw/content/sjtu-news.json"
    "database/raw/content/sjtu-gs.json"
    "database/raw/content/sjtu-lib.json"
    "database/raw/content/sjtu-seiee.json"
    "database/raw/content/sjtu-bme.json"
    "database/raw/content/sjtu-aero.json"
    "database/raw/content/sjtu-physics.json"
    "database/raw/content/sjtu-scce.json"
    "database/raw/content/sjtu-soo.json"
    "database/raw/content/sjtu-agri.json"
    "database/raw/content/sjtu-pharm.json"
    "database/raw/content/sjtu-law.json"
    "database/raw/content/sjtu-sfl.json"
    "database/raw/content/sjtu-shss.json"
    "database/raw/content/sjtu-sipa.json"
    "database/raw/content/sjtu-smc.json"
    "database/raw/content/sjtu-designschool.json"
    "database/raw/content/sjtu-saif.json"
    "database/raw/content/sjtu-speit.json"
    "database/raw/content/sjtu-ji.json"
)

# 输出目录
# Output directory
output_dir="database/raw"

# 检查两个数组的长度是否相同
# Check if the lengths of the two arrays are the same
if [ "${#target_urls[@]}" -ne "${#json_paths[@]}" ]; then
    echo "Error: The lengths of target_urls and json_paths arrays do not match."
    exit 1
fi

# 遍历数组中的每个元素
# Iterate over each element in the arrays
for index in "${!target_urls[@]}"; do
    url="${target_urls[$index]}"
    json_path="${json_paths[$index]}"

    echo "Processing URL: $url"
    echo "Output JSON path: $json_path"

    # 重复执行5次
    # Repeat execution 5 times
    for run in {1..5}; do
        echo "  Starting run number $run for URL: $url..."

        python data_scrapper.py --extract-site --debug --target-url "$url" --output-dir "$output_dir" --json-path "$json_path"

        # 检查命令是否成功执行
        # Check if the command was executed successfully
        if [ $? -ne 0 ]; then
            echo "  Command failed for URL: $url on run number $run. Continuing to the next run."
            continue
        fi

        echo "  Finished run number $run for URL: $url."
        echo "  -----------------------------"
    done

    echo "Completed processing for URL: $url."
    echo "============================="
done

echo "All tasks completed."
