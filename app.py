import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from pydub import AudioSegment
import io

# --- 1. SECURE CLOUD DATABASE CONNECTION ---
@st.cache_resource
def init_db():
    """
    Initializes Firestore and handles RSA Private Key formatting 
    to prevent PEM 'InvalidByte' errors.
    """
    try:
        if "firebase" in st.secrets:
            # Load credentials from Streamlit Secrets
            info = dict(st.secrets["firebase"])
            # Auto-cleaning the PEM key for valid RSA handshake
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()

# --- 2. AI SPEECH-TO-TEXT PROCESSING ---
def convert_voice_to_text(audio_bytes):
    """
    Converts captured microphone audio (WebM) into WAV 
    and then uses Google AI to transcribe it into text.
    """
    try:
        # Convert audio bytes to a format the AI understands (WAV)
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            # Capture data from the converted WAV file
            audio_data = recognizer.record(source)
            # Use Google Speech Recognition API (Supporting English-India)
            text = recognizer.recognize_google(audio_data, language="en-IN")
            return text
    except Exception as e:
        return f"AI Transcription Error: {e}"

# --- 3. UI LAYOUT & NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
st.sidebar.caption("Real-time Multilingual Sync System")
app_mode = st.sidebar.radio("Navigation:", ["Student Portal", "Teacher Control"])

# --- 4. TEACHER CONTROL MODULE ---
if app_mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    st.write("Record your lecture. The AI will sync it to the Student Portal.")

    # Live Attendance Tracker (Fetched from Cloud)
    st.subheader("📋 Verified Student Attendance")
    if db:
        docs = db.collection("attendance").stream()
        attendance_list = [doc.to_dict() for doc in docs]
        if attendance_list:
            st.table(pd.DataFrame(attendance_list)[['Name', 'Roll']])
        else:
            st.info("Waiting for students to join...")

    st.divider()

    # Audio Capture & AI Transcription
    st.subheader("🔊 Live Lecture Recording")
    # Capture voice from the browser microphone
    audio_capture = mic_recorder(start_prompt="▶️ Start Lecture", stop_prompt="🛑 Stop & Process", key='mic')

    if audio_capture:
        with st.spinner("AI is processing your voice..."):
            # Process the audio bytes into text
            transcribed_text = convert_voice_to_text(audio_capture['bytes'])
            st.session_state.current_lecture = transcribed_text
            
            # Synchronize the text to Google Cloud Firestore
            if db:
                db.collection("lectures").document("current_session").set({
                    "content": transcribed_text,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("Lecture synced to Student Portal!")

    # Editable area for the Teacher to refine the AI output
    final_output = st.text_area("Teacher's Voice (Converted to Text):", 
                                value=st.session_state.get('current_lecture', ""), 
                                height=200)

    if st.button("📢 Update Students Immediately"):
        if db:
            db.collection("lectures").document("current_session").update({"content": final_output})
            st.success("Cloud Sync Successful!")

# --- 5. STUDENT PORTAL MODULE ---
elif app_mode == "Student Portal":
    st.header("👤 Student Access")
    
    # Attendance Section
    st.subheader("✍️ Mark Attendance")
    s_name = st.text_input("Full Name")
    s_roll = st.text_input("Roll Number")
    
    if st.button("Join Class"):
        if db and s_name and s_roll:
            db.collection("attendance").document(s_roll).set({
                "Name": s_name, "Roll": s_roll, "Status": "Present",
                "Timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("Attendance verified and synced!")

    st.divider()

    # Real-time Lecture Updates
    st.subheader("📖 Live Class Content")
    if db:
        # Fetching data from the 'lectures' collection updated by the Teacher
        lecture_ref = db.collection("lectures").document("current_session").get()
        if lecture_ref.exists:
            current_notes = lecture_ref.to_dict().get("content", "Waiting for teacher to start...")
            st.info(current_notes) # This is where the Student sees the Teacher's voice as text
        else:
            st.write("Lecture not started yet.")
