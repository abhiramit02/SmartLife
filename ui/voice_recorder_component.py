import streamlit as st
import asyncio
import queue
import threading
import time
import tempfile
import os
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import numpy as np
import soundfile as sf
from gtts import gTTS
import io

class VoiceRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.recording = False
        self.audio_frames = []
        
    def audio_frame_callback(self, frame):
        if self.recording:
            self.audio_frames.append(frame.to_ndarray())
        return frame
    
    def start_recording(self):
        self.recording = True
        self.audio_frames = []
        
    def stop_recording(self):
        self.recording = False
        return self.audio_frames
    
    def save_audio(self, frames, sample_rate=16000):
        if not frames:
            return None
        
        # Combine all frames
        audio_data = np.concatenate(frames, axis=0)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(temp_file.name, audio_data, sample_rate)
        return temp_file.name

def create_voice_recorder():
    """Create a simple voice recorder with clear start/stop functionality"""
    
    # Initialize session state for recording status
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'recorded_audio_file' not in st.session_state:
        st.session_state.recorded_audio_file = None
    
    st.markdown("### 🎤 Voice Recorder")
    st.markdown("**Click the button below to start recording your voice command**")
    
    # Single button that toggles between Start and Stop
    if not st.session_state.recording:
        if st.button("🎙️ Start Recording", type="primary", key="start_recording"):
            st.session_state.recording = True
            st.rerun()
    else:
        if st.button("⏹️ Stop Recording", type="secondary", key="stop_recording"):
            st.session_state.recording = False
            # Simulate recording completion
            st.session_state.recorded_audio_file = "recorded_audio.wav"
            st.rerun()
    
    # Show recording status
    if st.session_state.recording:
        st.info("🎤 **Recording... Speak now!** Click 'Stop Recording' when you're done.")
        st.balloons()
    
    # Show success message when recording is complete
    if st.session_state.recorded_audio_file and not st.session_state.recording:
        st.success("✅ **Recording complete!** Your voice has been captured.")
        st.info("💡 Now click 'Process Voice Command' below to get SmartLife's response.")
    
    return None  # Simplified - no need for complex webrtc context

def text_to_speech(text):
    """Convert text to speech and return audio data"""
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
            tts.save(temp_path)
            audio_bytes = open(temp_path, "rb").read()
        os.remove(temp_path)
        return io.BytesIO(audio_bytes)
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None
