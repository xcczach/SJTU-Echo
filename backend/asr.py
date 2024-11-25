from scipy.signal import resample
from funasr_onnx.utils.postprocess_utils import rich_transcription_postprocess
import numpy as np
from funasr_onnx import SenseVoiceSmall

def get_asr_model():
    return SenseVoiceSmall("iic/SenseVoiceSmall", batch_size=10, quantize=True)

def inference(audio_data: list[float], sample_rate: float, model: SenseVoiceSmall) -> str:
    audio = np.array(audio_data, dtype=np.float64)
    model_sr = model.frontend.opts.frame_opts.samp_freq
    if sample_rate != model_sr:
        audio = resample(audio, int(len(audio) * model_sr / sample_rate))
    result = model(audio, language="auto", use_itn=True)[0]
    result = rich_transcription_postprocess(result)
    return result