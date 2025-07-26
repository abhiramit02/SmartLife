import os
import io
import wave
import tempfile
import streamlit as st
from gtts import gTTS
import torch
import torchaudio
from transformers import (
    AutoProcessor, AutoModelForSpeechSeq2Seq,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration
)
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

DEVICE = "cpu"
SAMPLE_RATE = 16000

@st.cache_resource
def load_models():
    whisper_processor = AutoProcessor.from_pretrained("openai/whisper-tiny.en")
    whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-tiny.en").to(DEVICE)

    blender_tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
    blender_model = BlenderbotForConditionalGeneration.from_pretrained("facebook/blenderbot-400M-distill").to(DEVICE)

    return {
        "whisper": (whisper_processor, whisper_model),
        "blender": (blender_tokenizer, blender_model)
    }

def speech_to_text(audio_path, processor, model):
    speech_array, sr = torchaudio.load(audio_path)
    if sr != SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=SAMPLE_RATE)
        speech_array = resampler(speech_array)
    inputs = processor(speech_array.squeeze(), sampling_rate=SAMPLE_RATE, return_tensors="pt").to(DEVICE)
    predicted_ids = model.generate(**inputs, max_new_tokens=128, num_beams=3, early_stopping=True)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription.strip()

def get_response_from_model(user_input, tokenizer, model):
    inputs = tokenizer(user_input, return_tensors="pt").to(DEVICE)
    outputs = model.generate(**inputs, max_new_tokens=80, num_beams=3, early_stopping=True)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

def speak_response(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
    os.remove(fp.name)
    return io.BytesIO(audio_bytes)

def run_voice_assistant(uploaded_file):
    """Existing upload-based flow (expects a Streamlit UploadedFile)."""
    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    if uploaded_file is None:
        return None, None, "⚠️ Please upload a WAV audio file."

    if uploaded_file.type != "audio/wav":
        return None, None, "⚠️ Please upload a valid WAV audio file."

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        command = speech_to_text(tmp_path, whisper_processor, whisper_model)
        reply = get_response_from_model(command, blender_tokenizer, blender_model)
        audio_data = speak_response(reply)

        os.remove(tmp_path)
        return audio_data, command, reply

    except Exception as e:
        return None, None, f"⚠️ Processing Error: {e}"

class AudioRecorder(AudioProcessorBase):
    """Collect raw PCM int16 audio from the browser."""
    def __init__(self) -> None:
        self.audio_bytes = b""

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # Convert to int16 PCM bytes and accumulate
        pcm = frame.to_ndarray().tobytes()
        self.audio_bytes += pcm
        return frame

def save_pcm_to_wav(pcm_bytes: bytes, path: str, sample_rate: int = SAMPLE_RATE, channels: int = 1, sampwidth: int = 2):
    """Write raw PCM bytes to a valid WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)  # 2 bytes for int16
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)

def run_voice_assistant_from_wav_path(wav_path: str):
    """Shared STT → LLM → TTS pipeline for a ready WAV file path."""
    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    command = speech_to_text(wav_path, whisper_processor, whisper_model)
    reply = get_response_from_model(command, blender_tokenizer, blender_model)
    audio_data = speak_response(reply)
    return audio_data, command, reply
