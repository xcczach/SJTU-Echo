import argparse
from backend.server import launch_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat-model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--vectorstore-source-dir", type=str, default="test_output/sample_embeddings")
    parser.add_argument("--port", type=int, default=9834)
    args = parser.parse_args()

    launch_server(args.chat_model, args.vectorstore_source_dir, args.port)
