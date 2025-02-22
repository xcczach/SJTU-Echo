import argparse
from backend.server import launch_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat-model", type=str, default="Qwen/Qwen2.5-32B-Instruct-AWQ")
    parser.add_argument("--vectorstore-source-dir", type=str, default="test_output/sample_embeddings")
    parser.add_argument("--port", type=int, default=9834)
    parser.add_argument("--llm-gpu-memory-utilization", type=float, default=0.6)
    parser.add_argument("--rag-strategy", type=str, default="hypothetical_question")
    args = parser.parse_args()

    launch_server(args.chat_model, args.vectorstore_source_dir, args.port, args.rag_strategy, args.llm_gpu_memory_utilization)
