# SJTU-Echo
Voice QA agent for SJTU campus guide

## Collaborators
- [Zhanxun Liu](xcc_zach@sjtu.edu.com)
- [Yaohui Chen](1009283848@sjtu.edu.cn)
- [Yunhao Yi](yiyunhao@sjtu.edu.cn)
- [Yinshen Wu](wuyinshen@sjtu.edu.cn)
- [Junhao Li](Lijunhao_hz@sjtu.edu.cn)

## Development Guidance
- Work in individual branches like "name" or "name-function"
- Better use pull request to merge to the main branch

## Tasks
- [ ] SJTU data scrapping
- [ ] LLM
- [ ] RAG
- [ ] Text to speech
- [ ] Speech to text
- [ ] UI

## Usage

### Data scrapping

Currently only support running on windows.

Extract links from a certain website recursively:
```bash
python data_scrapper.py --extract-links
```

Extract sub-urls (urls starting with the same base url) from a base url:
```bash
python data_scrapper.py --extract-sub-urls
```

Extract content from a list of websites:
```bash
python data_scrapper.py --extract-content
```

### Embedding

Embed content from a json file (created by `--extract-content`):
```bash
python embedder.py --content-json-path output/sample_content.json --output-dir output/sample_embeddings
```

## Examples

### RAG

```bash
python test_rag.py
```
