from ragas import SingleTurnSample,EvaluationDataset
from ragas.metrics import LLMContextPrecisionWithoutReference,SemanticSimilarity,ResponseRelevancy,LLMContextRecall, Faithfulness
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import os
from backend.rag import inference as rag_inference, RAGStrategy
from tqdm.auto import tqdm
from typing import Literal
from utils.models import QwenModel
from backend.rag import get_hf_vectorstore
from langchain_core.messages import HumanMessage
from timeit import default_timer as timer

class RAGResult:
    def __init__(self, question: str, retrieved_context: list[str], response: str):
        self.question = question
        self.retrieved_context = retrieved_context
        self.response = response

def _eval_rag_results(rag_results: list[RAGResult]):
    api_base = os.getenv("OPENAI_API_BASE") or None
    chat_model = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_base=api_base
    )
    def get_single_turn_sample(rag_result: RAGResult):
        context = "".join(rag_result.retrieved_context)
        prompt = f"""
        Based on the given context, answer the question concisely.
        Context: {context}
        Question: {rag_result.question}
        Answer:
        """
        ground_truth = chat_model.invoke(prompt).content
        ground_truth = ground_truth.strip()
        return SingleTurnSample(
            user_input=rag_result.question,
            retrieved_contexts=rag_result.retrieved_context,
            response=rag_result.response,
            reference=ground_truth,
        )
    samples = [get_single_turn_sample(rag_result) for rag_result in tqdm(rag_results, desc="Creating ChatGPT ground truths")]
    dataset = EvaluationDataset(samples=samples)

    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_base=api_base
    ))
    evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_base=api_base
    ))
    metrics = [
        LLMContextRecall(llm=evaluator_llm), #It focuses on not missing important results. 
        Faithfulness(llm=evaluator_llm),#For each of the generated statements, verify if it can be inferred from the given context.
        ResponseRelevancy(llm=evaluator_llm,embeddings=evaluator_embeddings),#Calculate the mean cosine similarity between the generated questions and the actual question.
        SemanticSimilarity(embeddings=evaluator_embeddings),
        LLMContextPrecisionWithoutReference(llm=evaluator_llm)
    ]

    results = evaluate(dataset=dataset, metrics=metrics)

    df=results.to_pandas()

    statistics = [
        "context_recall",
        "faithfulness",
        "answer_relevancy",
        "semantic_similarity",
        "llm_context_precision_without_reference"
    ]
    mean_df = df.mean(numeric_only=True)
    return { "df":df,"mean":mean_df[statistics].to_dict() }

def _get_questions(file_name: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    questions_file = os.path.join(current_dir, file_name)
    with open(questions_file, "r") as f:
        questions = f.readlines()
    questions = [question.strip() for question in questions]
    return questions

def eval_rag_strategy(strategy: RAGStrategy | Literal["nothing"], vectorstore_path: str = "test_output/sample_embeddings", questions_file: str="sample_questions.txt", evaluation_model: str="Qwen/Qwen2.5-1.5B-Instruct", llm_gpu_memory_utilization: float = 0.6):
    def strategy_nothing(question: str):
        return "", [""]
    rag_results = []
    questions = _get_questions(questions_file)
    if strategy != "nothing":
        chat_model = QwenModel(model=evaluation_model, gpu_memory_utilization=llm_gpu_memory_utilization)
        vectorstore = get_hf_vectorstore(vectorstore_path)
    rag_start_time = timer()
    for question in tqdm(questions, desc="RAG generation"):
        if strategy == "nothing":
            response, retrieved_context = strategy_nothing(question)
        else:
            inferenced_message, retrieved_context = rag_inference([HumanMessage(content=question)], chat_model, vectorstore, strategy)
            response = inferenced_message.content
        rag_results.append(RAGResult(question=question, retrieved_context=retrieved_context, response=response))
    rag_time_elapsed = timer() - rag_start_time
    rag_time_per_question = rag_time_elapsed / len(questions)
    rag_eval_results = _eval_rag_results(rag_results)
    rag_eval_results["time_per_question"] = rag_time_per_question
    return rag_eval_results

def test_rag(strategy: RAGStrategy, vectorstore_path: str="test_output/sample_embeddings",question: str="上海市第八届优秀网站评选活动网上投票何时启动？", evaluation_model: str="Qwen/Qwen2.5-1.5B-Instruct", llm_gpu_memory_utilization: float = 0.6):
    chat_model = QwenModel(model=evaluation_model, gpu_memory_utilization=llm_gpu_memory_utilization)
    vectorstore = get_hf_vectorstore(vectorstore_path)
    inferenced_message, retrieved_context = rag_inference([HumanMessage(content=question)], chat_model, vectorstore, strategy)
    response = inferenced_message.content
    return response, retrieved_context
