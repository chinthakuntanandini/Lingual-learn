import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io
from pydub import AudioSegment

# --- 1. FIREBASE CONNECTION (With Key Cleaning) ---
@st.cache_resource
def init_db():
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            # Fixing the PEM formatting issue (InvalidByte fix)
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()

# --- UI NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
mode = st.sidebar.radio("Navigation:", ["Student Portal", "Teacher Control"])

# --- TEACHER CONTROL ---
if mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    st.subheader("🎙️ AI Lecture Capture")
    
    # Recording Logic
    audio_data = mic_recorder(start_prompt="▶️ Start Speaking", stop_prompt="🛑 Stop & Process", key='teacher_mic')
    
    if audio_data:
        try:
            # 1. Convert Audio Bytes to WAV format using pydub
            audio_bytes = audio_data['bytes']
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)
            
            # 2. Speech to Text AI Logic
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_io) as source:
                recorded_audio = recognizer.record(source)
                # Recognize Speech (English + Telugu Support)
                text = recognizer.recognize_google(recorded_audio, language="en-IN") 
                st.session_state.lecture_content = text
                
                # 3. Sync to Cloud
                if db:
                    db.collection("lectures").document("current_session").set({
                        "content": text,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("Voice successfully converted and synced to Cloud!")
        except Exception as e:
            st.error(f"AI Error: {e}. Try speaking clearly into the mic.")

    # Displaying the converted text
    final_notes = st.text_area("Teacher's Voice (Converted to Text):", 
                               value=st.session_state.get('lecture_content', ""), 
                               height=150)
    
    if st.button("Update Students"):
        if db:
            db.collection("lectures").document("current_session").update({"content": final_notes})
            st.success("Notes Updated!")

# --- STUDENT PORTAL ---
elif mode == "Student Portal":
    st.header("👤 Student View")
    st.subheader("📖 Live Class Notes")
    if db:
        lecture_ref = db.collection("lectures").document("current_session").get()
        if lecture_ref.exists:
            st.info(lecture_ref.to_dict().get("content", "Waiting for teacher to speak..."))
