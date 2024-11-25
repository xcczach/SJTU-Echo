import requests
import timeit
import soundfile as sf
import io

if __name__ == "__main__":
    url = "http://localhost:9834/rag"
    data = {"messages": [{"type": "human", "content": "科技创新行动计划的申报要求是什么？", "response_metadata": {}}]}
    start = timeit.default_timer()
    response = requests.post(url, json=data)
    end = timeit.default_timer()
    print(f"RAG Time elapsed: {end - start}")
    print(response.json())
    # should print something like:
    # {'messages': [{'type': 'ai', 'content': '科技创新行动计划的申报要求主要包括：\n1. 研究内容已经获得财政资金支持的，不得重复申报。\n2. 所有申报单位和项目参与人应遵守科研伦理准则，遵守人类遗传资源管理相关法规，符合科研诚信管理要求。\n3. 申报项目若提出回避专家申请的，须在提交项目可行性方案的同时，上传由申报单位出具公函提出回避专家名单与理由。\n4. 已作为项目负责人承担市科委科技计划在研项目2项及以上者，不得作为项目负责人申报。\n5. 项目经费预算编制应当真实、合理，符合市科委科技计划项目经费管理的有关要求。\n6. 申报主体要求：本市法人或非法人组织。\n7. 申报方向：区块链技术研究、元宇宙技术研究。\n8. 申报要求：项目（课题）负责人限申报1个项目（课题），国家科技重大专项、国家重点研发计划、科技创新2030—重大项目的在研项目负责人不得牵头或参与申报项目（课题）。\n9. 需提供单位自筹的，请学院和项目组协商解决，并出具学院盖章承诺，学校据此出具盖有校印的自筹证明。\n10. 项目申报单位、项目参与单位以及项目团队成员诚信状况良好，无在惩戒执行期内的科研严重失信行为记录和相关社会领域信用“黑名单”记录。', 'response_metadata': {'link': 'https://www.sjtu.edu.cn/tg/20210210/141161.html'}}]}

    url = "http://localhost:9834/tts"
    # data = {"text": "Chtholly Nota Seniorious is the main female protagonist of the light novel series \"WorldEnd: What do you do at the end of the world? Are you busy? Will you save us?\" She is a Leprechaun fairy soldier and the wielder of the powerful holy sword \"Seniorious.\" Throughout the story, Chtholly develops a deep bond with the male lead, Willem Kmetsch, and faces numerous challenges, including the erosion of her past memories."}
    data = {"text": "珂朵莉是世界上最幸福的女孩"}
    start = timeit.default_timer()
    response = requests.post(url, json=data, stream=True)
    if response.status_code == 200:
        audio_chunks = []

        buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=4096):
            buffer.write(chunk)

        buffer.seek(0)
        audio_data, sample_rate = sf.read(buffer)
        sf.write("output_audio.wav", audio_data, sample_rate)

        end = timeit.default_timer()
        print(f"TTS Time elapsed: {end - start}")
        print("Sample tts audio saved at output_audio.wav")
    else:
        print(f"Bad request：{response.status_code}")

    url = "http://localhost:9834/asr"
    audio_data, sample_rate = sf.read("output/ref_audio.mp3")
    data = {"sample_rate": sample_rate, "audio_data": audio_data.tolist()}
    start = timeit.default_timer()
    response = requests.post(url, json=data, stream=True)
    if response.status_code == 200:
        end = timeit.default_timer()
        print(f"TTS Time elapsed: {end - start}")
        print(response.text)
    else:
        print(f"Bad request：{response.status_code}")