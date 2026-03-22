import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io

# --- 1. DATABASE CONNECTION ---
@st.cache_resource
def init_db():
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            # Auto-rectifying the PEM formatting
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

# --- STUDENT PORTAL ---
if mode == "Student Portal":
    st.header("👤 Student View")
    st.subheader("📖 Live Class Notes (From Teacher)")
    if db:
        # Teacher పంపిన లైవ్ నోట్స్ ఇక్కడ కనిపిస్తాయి
        lecture_ref = db.collection("lectures").document("current_session").get()
        if lecture_ref.exists:
            st.info(lecture_ref.to_dict().get("content", "Waiting for teacher..."))

# --- TEACHER CONTROL ---
elif mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    
    st.subheader("🎙️ AI Lecture Capture")
    st.write("మాట్లాడటం అయ్యాక 'Stop' నొక్కండి, అప్పుడు అది టెక్స్ట్‌గా మారుతుంది:")
    
    # Recording Logic
    audio_data = mic_recorder(start_prompt="▶️ Start Speaking", stop_prompt="🛑 Stop & Convert to Text", key='teacher_mic')
    
    if audio_data:
        # టీచర్ మాట్లాడిన వాయిస్‌ని టెక్స్ట్‌గా మార్చే AI లాజిక్
        recognizer = sr.Recognizer()
        try:
            audio_bytes = io.BytesIO(audio_data['bytes'])
            with sr.AudioFile(audio_bytes) as source:
                audio = recognizer.record(source)
                # Convert Speech to Text (English/Telugu support)
                text = recognizer.recognize_google(audio) 
                st.session_state.lecture_content = text
                
                # Cloud లో సేవ్ చేయడం (స్టూడెంట్ కి పంపడానికి)
                if db:
                    db.collection("lectures").document("current_session").set({
                        "content": text,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("Voice successfully converted to text and synced!")
        except Exception as e:
            st.error(f"AI could not understand the audio: {e}")

    # టీచర్ మాట్లాడిన మాటలు ఇక్కడ కనిపిస్తాయి
    final_notes = st.text_area("Teacher's Voice (Converted to Text):", 
                               value=st.session_state.get('lecture_content', ""), 
                               height=150)
    
    if st.button("Update to All Students"):
        if db:
            db.collection("lectures").document("current_session").update({"content": final_notes})
            st.success("Updated Successfully!")
