from ragas import SingleTurnSample,EvaluationDataset
from ragas.metrics import LLMContextPrecisionWithoutReference,SemanticSimilarity,ResponseRelevancy,LLMContextRecall, Faithfulness
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import os
from typing import Callable,Literal

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
    samples = [get_single_turn_sample(rag_result) for rag_result in rag_results]
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

def _get_default_questions():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    questions_file = os.path.join(current_dir, "sample_questions.txt")
    with open(questions_file, "r") as f:
        questions = f.readlines()
    questions = [question.strip() for question in questions]
    return questions

RAGStrategy = Literal["nothing", "hypothetical_question"]

def eval_rag_strategy(strategy: Callable[[str], tuple[str,list[str]]] | RAGStrategy, questions: list[str]=_get_default_questions()):
    if isinstance(strategy, str):
        strategy = globals()["_strategy_"+strategy]
    
    rag_results = []
    for question in questions:
        response, retrieved_context = strategy(question)
        rag_results.append(RAGResult(question=question, retrieved_context=retrieved_context, response=response))
    return _eval_rag_results(rag_results)

def _strategy_hypothetical_question(question: str):
    pass

def _strategy_nothing(question: str):
    return "", [""]