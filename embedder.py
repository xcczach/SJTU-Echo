from data_utils.embedder import create_vectorstore_from_huggingface
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-json-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--embedding-model", type=str, default="Alibaba-NLP/gte-Qwen2-1.5B-instruct")