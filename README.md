# SJTU-Echo
Voice QA agent for SJTU campus guide

The instructions below may be out-of-date. You can contact [the author](xcc_zach@sjtu.edu.com) with email for help!

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

(Optional) Change the locations to download model checkpoints (you need to add the environment variables to your .bashrc to permanently set them):
```bash
export HF_HOME="<target_dir>"
export MODELSCOPE_CACHE="<target_dir>"
```

Download the TTS checkpoint:
```bash
export HF_ENDPOINT="https://hf-mirror.com" # Optional, may be necessary if you are in China
python ckpts/download.py
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

### Filter scrapped links

Filter scrapped links by a list of prefixes:

```bash
python filter_links.py --file-path <file-containing-links> --link-prefixes <prefixes> --output-path <output-json-path>
```

### Merge scrapped web content

Merge several json files with scrapped content into one:

```bash
python merge_content.py --json-paths <files-to-merge> --output-path <output-directory>
```

Example:

```bash
python merge_content.py --json-paths database/raw/content/sjtu.json database/raw/content/sjtu-ji.json --output-path database/raw/content/sjtu_sjtu-ji.json
```

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

### Start server/backend

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

If you meet GPU Out of Memory error, you can try to lower the `--llm-gpu-memory-utilization` setting.

### Start frontend

Follow the instructions in `page/README.md`. Remember to change the configurations in `page/src/components/ServerConfig.js`, as mentioned in `page/README.md`.

You can select the embeddings used with `--vectorstore-source-dir`, and you need to use the strategy for the embeddings you selected with `--rag-strategy`.

## Examples

### RAG

*Git LFS needed!*

`git lfs pull` to get the `sample_content.json` file.

First create sample embeddings if not exist:
```bash
python embedder.py --content-json-path test_output/sample_content.json --output-dir test_output/sample_embeddings
```

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

## Contact

- [Zhanxun Liu](xcc_zach@sjtu.edu.com)
- [Yaohui Chen](1009283848@sjtu.edu.cn)
- [Yunhao Yi](yiyunhao@sjtu.edu.cn)
- [Yinshen Wu](wuyinshen@sjtu.edu.cn)
- [Junhao Li](Lijunhao_hz@sjtu.edu.cn)