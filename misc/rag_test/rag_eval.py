from ragas import SingleTurnSample,EvaluationDataset
from ragas.metrics import LLMContextPrecisionWithoutReference,SemanticSimilarity,ResponseRelevancy,LLMContextRecall, Faithfulness
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import OpenAIEmbeddings
# 设置 OpenAI API 密钥

from langchain_openai import ChatOpenAI

def ragas(question,retrieved_context,response):
    chat_model = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_base='https://xiaoai.plus/v1'
    )
    question=question
    context="".join(retrieved_context)
    prompt = f"""
    Based on the given context, answer the question concisely.
    Context: {context}
    Question: {question}
    Answer:
    """
    ground_truth = chat_model.predict(prompt)
    ground_truth = ground_truth.strip()

    #line for test
    # print("-----------------\n"+question+"\n"+context+"\n"+ground_truth+"\n"+response)

    # Sample
    sample = SingleTurnSample(
        user_input=question,
        retrieved_contexts=retrieved_context,
        response=response,
        reference=ground_truth,
    )
    #dataset
    dataset = EvaluationDataset(samples=[sample])

    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_base='https://xiaoai.plus/v1'
    ))
    evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_base='https://xiaoai.plus/v1'
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
    context_recall = df.loc[0, "context_recall"]
    faithfulness = df.loc[0, "faithfulness"]
    response_relevancy = df.loc[0, "answer_relevancy"]
    semantic_similarity= df.loc[0, "semantic_similarity"]
    context_precision= df.loc[0, "llm_context_precision_without_reference"]

#下面是返回的值，可以根据需要修改输出
    print("Context Recall:", round(context_recall, 2))
    print("Faithfulness:", round(faithfulness, 2))
    print("Response Relevancy:", round(response_relevancy, 2))
    print("Semantic Similarity:", round(semantic_similarity, 2))
    print("Context Precision:", round(context_precision, 2))

def main():
    #先pip install ragas
    #设置openai密钥

    #用户输入的问题
    question="What is the capital of France?"
    #从DATASET中召回的文本，存入数组中
    retreived_context=["Paris is the capital.","Paries is the most populous city of France."]
    #RAG生成的回答
    response="The capital of France is Paris."

    #在RAG里写一个函数得到上面三个变量,用下面这个函数得到最后的结果，现在输出是Print,可以根据需要调整
    ragas(question,retreived_context,response)
if __name__ == "__main__":
    main()



