## Usage
### 1
Extract all sub-urls from a target url:
```bash
python .\main.py --extract-sub-urls-from <target_url>
```
Example
```bash
python .\main.py --extract-sub-urls-from https://www.seiee.sjtu.edu.cn/
```
### 2
Extract content from target urls:
```bash
python .\main.py --extract-content-from list<target_url>
```
Example
```bash
python .\main.py --extract-content-from https://www.sjtu.edu.cn/ https://www.sjtu.edu.cn/tg/20241031/203492.html https://www.sjtu.edu.cn/tg/20241025/203256.html
```
Current extraction strategy:
- Extract content of all urls from their static html source, use *readability* to get the main content
- If length of the extracted content is less than a threshold, extract content dynamically using selenium, and return the whole raw web page content