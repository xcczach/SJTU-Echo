import re
import torchaudio
from io import BytesIO
from torch import tensor, cat
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from ml_web_inference import get_proper_device
import os

def _get_wav_path(path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_wavs", path)

_lang_to_sample_path = {
    "en": _get_wav_path("en_sample.wav"),
    "zh": _get_wav_path("zh-cn-sample.wav"),
    "ja": _get_wav_path("ja-sample.wav"),
}

def _detect_language(text):
    if re.search(r'[\u4e00-\u9fff]', text):
        return "zh"
    if re.search(r'[a-zA-Z]', text):
        return "en"
    if re.search(r'[\u3040-\u30ff]', text):
        return "ja"
    return "unknown"
    
def get_tts_model_and_config():
    config = XttsConfig()
    config.load_json("ckpts/xttsv2/config.json")
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir="ckpts/xttsv2", eval=True)
    model.to(get_proper_device(2000))
    return model, config
    
def _get_result_arr(text: str, model, config, lang: str):
    result_dict = model.synthesize(
        text,
        config,
        speaker_wav=_lang_to_sample_path[lang],
        language=lang,
        gpt_cond_len=10
    )
    return tensor(result_dict["wav"])

def _split_text_multilang(text, threshold, lang='zh'):
    if lang == 'zh' or lang == 'jp':
        sentences = re.split(r'(，|。|！|？|；|：|…)', text)
        segments = []
        temp_segment = ""
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                part = sentences[i] + sentences[i + 1]
            else:
                part = sentences[i]
            if len(temp_segment) + len(part) <= threshold:
                temp_segment += part
            else:
                if temp_segment:
                    segments.append(temp_segment)
                temp_segment = part
        if temp_segment:
            segments.append(temp_segment)

    elif lang == 'en':
        words = text.split()
        segments = []
        temp_segment = []
        for word in words:
            if len(temp_segment) + 1 <= threshold:
                temp_segment.append(word)
            else:
                if temp_segment:
                    segments.append(' '.join(temp_segment))
                temp_segment = [word]
        if temp_segment:
            segments.append(' '.join(temp_segment))

    else:
        segments = [text]
    
    # remove duplicate segments
    segments = list(dict.fromkeys(segments))
    return segments

_lang_segment_threshold = {
    "en": 40,
    "zh": 40,
    "ja": 40,
}
def inference(text: str, model, config):
    lang = _detect_language(text)
    text_segments = _split_text_multilang(text, _lang_segment_threshold[lang], lang)
    result_arrs = []
    for segment in text_segments:
        result_arrs.append(_get_result_arr(segment, model, config, lang))
    result_arr = cat(result_arrs)
    result = BytesIO()
    torchaudio.save(result, result_arr.unsqueeze(0), 24000, format="wav")
    result.seek(0)
    return result