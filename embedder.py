from data_utils.embedder import save_vectorstore_from_huggingface, EmbeddingStrategy
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-json-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--strategy", type=str, default="hypothetical_question")
    parser.add_argument("--embedding-model", type=str, default="Alibaba-NLP/gte-Qwen2-1.5B-instruct")
    args = parser.parse_args()

    print(f"Embedding strategy: {args.strategy}")
    print(f"Embedding strategies available: {EmbeddingStrategy.__args__}")
    save_vectorstore_from_huggingface(args.content_json_path, args.output_dir, args.embedding_model, args.strategy)
    print("Vectorstore saved to", args.output_dir)