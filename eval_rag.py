from rag_eval.rag_eval import eval_rag_strategy, RAGStrategy
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, default="nothing")
    parser.add_argument("--small-questions", action="store_true")
    args = parser.parse_args()
    
    print(f" RAG strategies: {RAGStrategy.__args__ + ('nothing',)}")
    print(f" Evaluating strategy: {args.strategy}")
    if args.small_questions:
        print(" Using small questions set")
        questions_file = "sample_questions_small.txt"
    else:
        questions_file = "sample_questions.txt"
    eval_result = eval_rag_strategy(args.strategy, questions_file)
    eval_statistics = eval_result["mean"]
    result_file_name = f"test_output/eval_results/eval_results_{args.strategy}{'_small_questions' if args.small_questions else ''}.out"
    with open(result_file_name, "w") as f:
        f.write(f"Results for {args.strategy}:\n")
        for key, value in eval_statistics.items():
            f.write(f"{key}: {value}\n")
    print(f"Evaluation completed. Results saved to {result_file_name}")