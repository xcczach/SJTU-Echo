from datasets import Dataset
import sys
import os
os.environ["输入openai_key"]
# 确保 test_pipeline 可以被导入
sys.path.append("/root/SJTU-Echo/misc/rag_test")
from test_pipeline import get_answer_and_retrieved_text

questions=["交大之星通知是什么？"]
ground_truths=["上海交通大学发布的“交大之星”计划“医工交叉研究基金”2025年度申报指南通知，旨在促进医学与工科、理科等学科的交叉融合，推动临床需求驱动的多学科交叉研究，提升临床水平和创新能力。通知要求各申报单位的科研管理部门在2024年11月25日前提交申请材料，并提供相关的附件。"]
answers=[]
contexts=[]

for question in questions:
    answer, retrieved_text = get_answer_and_retrieved_text(question, "/root/SJTU-Echo/misc/rag_test/data/sample_contents.json")
    answers.append(answer)
    contexts.append(retrieved_text)

# 创建 Dataset 来进行评估等操作
dataset = Dataset.from_dict({"question": questions, "reference": ground_truths, "answer": answers, "contexts": contexts})

from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness, SemanticSimilarity
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-3.5-turbo"))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
metrics = [
    LLMContextRecall(llm=evaluator_llm), 
    FactualCorrectness(llm=evaluator_llm), 
    Faithfulness(llm=evaluator_llm),
    SemanticSimilarity(embeddings=evaluator_embeddings)
]
results = evaluate(dataset=dataset, metrics=metrics)

df=results.to_pandas()
df.head()



