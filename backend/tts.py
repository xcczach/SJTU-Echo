import re
import torchaudio
from io import BytesIO
from torch import tensor
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
    
def inference(text: str, model, config):
    lang = _detect_language(text)
    result_dict = model.synthesize(
        text,
        config,
        speaker_wav=_lang_to_sample_path[lang],
        language=lang,
        gpt_cond_len=3
    )
    result_arr = result_dict["wav"]
    result = BytesIO()
    torchaudio.save(result, tensor(result_arr).unsqueeze(0), 24000, format="wav")
    result.seek(0)
    return result