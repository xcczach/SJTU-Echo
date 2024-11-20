from ml_web_inference import (
    expose,
    Request,
    Response,
)
import torch
import io
import argparse
from scipy.signal import resample
from funasr_onnx.utils.postprocess_utils import rich_transcription_postprocess
import numpy as np
from funasr_onnx import SenseVoiceSmall

model = None


async def inference(request: Request) -> Response:
    data = await request.json()
    sample_rate = data["sample_rate"]
    audio_data = data["audio_data"]
    audio = np.array(audio_data, dtype=np.float64)

    model_sr = model.frontend.opts.frame_opts.samp_freq
    if sample_rate != model_sr:
        audio = resample(audio, int(len(audio) * model_sr / sample_rate))

    result = model(audio, language="auto", use_itn=True)[0]
    result = rich_transcription_postprocess(result)

    return Response(
        content=result,
        media_type="text/plain",
    )


def init():
    global model
    model = SenseVoiceSmall("iic/SenseVoiceSmall", batch_size=10, quantize=True)


def hangup():
    global model
    del model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9234)
    parser.add_argument("--api-name", type=str, default="asr")
    parser.add_argument("--hangup-timeout-sec", type=int, default=900)
    parser.add_argument("--hangup-interval-sec", type=int, default=60)
    args = parser.parse_args()
    expose(
        args.api_name,
        inference,
        port=args.port,
        hangup_timeout_sec=args.hangup_timeout_sec,
        hangup_interval_sec=args.hangup_interval_sec,
        init_function=init,
        hangup_function=hangup,
    )
