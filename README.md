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

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

Download the TTS checkpoint:
```bash
export HF_ENDPOINT="https://hf-mirror.com" # Optional, necessary if you are in China
python ckpts/download.py
```

(Optional) Change the locations to download model checkpoints:
```bash
export HF_HOME="<target_dir>"
export MODELSCOPE_CACHE="<target_dir>"
```

## Usage

### Data scrapping

If you are using Linux, you can install the Chrome & Chrome driver for Selenium with:
```bash
bash driver_install.sh
```

On Windows, you can search how to install Chrome and Chrome driver for Selenium.

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

Do `--extract-sub-urls` and `--extract-content` together:
```bash
python data_scrapper.py --extract-site
```

Options that can be specified: `--target-url`, `--output-dir`, `--depth`, `--urls-file-path`, `--json-path`.
If not specified, necessary parameters will be prompted for interactively.

Add `--debug` to print debug information.

### Embedding

Embed content from a json file (created by `--extract-content`):
```bash
python embedder.py --content-json-path test_output/sample_content.json --output-dir test_output/sample_embeddings
```

Add `--strategy` to customize the embedding strategy. Defaults to `hypothetical_question`. Run and see strategy options.

Add `--embedding-model` to customize the Huggingface embedding model. Defaults to `Alibaba-NLP/gte-Qwen2-1.5B-instruct`.

### RAG Evaluation

*Git LFS needed!*

`git lfs pull` to get the `sample_content.json` file.

First create sample embeddings if not exist:
```bash
python embedder.py --content-json-path test_output/sample_content.json --output-dir test_output/sample_embeddings
```

Then evaluate the RAG model:
```bash
export OPENAI_API_KEY=<your_openai_api_key>
export OPENAI_API_BASE=<your_openai_api_base> # if any
python eval_rag.py --strategy <strategy>
```

You can start with strategy `nothing` for test.

Add `--small-questions` to use the smaller question set.

Add `--vectorstore-path` to customize the vector store path. Defaults to `test_output/sample_embeddings`.

### Start server

*Git LFS needed!*

`git lfs pull` to get the `sample_content.json` file.

First create sample embeddings if not exist:
```bash
python embedder.py --content-json-path test_output/sample_content.json --output-dir test_output/sample_embeddings
```

Then start the default server:
```bash
python server.py
```

If you meet GPU Out of Memory error, you can try to lower the `--llm-gpu-memory-utilization` parameter.

## Examples

### RAG

```bash
python test_rag.py
```

### Sample API POST

*Git LFS needed!*

`git lfs pull` to get the `sample_content.json` file.

First create sample embeddings if not exist:
```bash
python embedder.py --content-json-path test_output/sample_content.json --output-dir test_output/sample_embeddings
```

Then start the default server:
```bash
python server.py
```

Then run the sample POST in another terminal:
```bash
python test_client.py
```
