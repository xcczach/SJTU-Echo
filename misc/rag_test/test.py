
import openai

def test_api_key(api_key):
    openai.api_key = api_key

    try:
        # 尝试使用API密钥获取模型列表
        models = openai.models.list()
        print("您的OpenAI API密钥是有效的。")
        print(models)
        return True
    except Exception as e:
        print(f"出现错误，可能是因为API密钥无效：{e}")
        return False

# 用您的实际API密钥替换这里的'YOUR_API_KEY'
your_api_key="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"
is_valid = test_api_key(your_api_key)


if is_valid:
    print("密钥测试通过。")
else:
    print("密钥测试失败，请检查您的API密钥。")
