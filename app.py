import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
from fpdf import FPDF
import io
import re

# --- 1. DATABASE CONNECTION (FIREBASE) ---
@st.cache_resource
def init_db():
    """Connects to Firestore using Streamlit Secrets. Handles PEM format errors."""
    try:
        if "firebase" in st.secrets:
            # Load credentials from secrets
            info = dict(st.secrets["firebase"])
            
            # CRITICAL FIX: Ensure the private key handles newlines correctly
            # This fixes the 'InvalidData(InvalidByte)' PEM error
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        # Displays the exact error if connection fails
        st.error(f"Firebase Connection Error: {e}")
    return None

db = init_db()

# Initialize Translator in Session State to avoid re-loading
if 'translator' not in st.session_state:
    st.session_state.translator = Translator()

# --- 2. PDF GENERATION LOGIC ---
def create_pdf(title, content_list):
    """Creates a simple PDF file from lecture notes."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for line in content_list:
        # Multi_cell handles long text wrapping
        pdf.multi_cell(0, 10, txt=str(line))
    return pdf.output(dest='S').encode('latin-1')

# --- 3. PAGE NAVIGATION ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔊 Live Lecture Capture")
        # Record audio from the browser
        audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Process", key='teacher_mic')
        
        if audio:
            recognizer = sr.Recognizer()
            try:
                # Process audio bytes
                audio_file = io.BytesIO(audio['bytes'])
                with sr.AudioFile(audio_file) as source:
                    # IMPROVEMENT: Noise adjustment for clearer speech recognition
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)
                    # Convert Voice to Text
                    text = recognizer.recognize_google(audio_data, language='en-IN')
                    st.session_state.master_notes = text
                    st.success("Voice Captured Successfully!")
            except Exception as e:
                st.error(f"Audio Error: {e}. Please speak clearly and check your mic.")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img_file = st.file_uploader("Upload Class Diagram", type=['jpg', 'png', 'jpeg'])
        if img_file:
            st.image(img_file, caption="Live Diagram", width=300)

    # --- TRANSCRIPT & TABLE LOGIC ---
    st.divider()
    st.subheader("📝 Current Transcript")
    # Show the text area for editing or viewing recorded notes
    current_notes = st.text_area("Review Lecture Content:", value=st.session_state.get('master_notes', ""), height=150)
    
    # SPEAK-TO-TABLE: Look for patterns like 'Science: 80' or 'Maths: 95'
    table_items = re.findall(r"([\w\s]+)\s*[:]\s*(\d+)", current_notes)
    if table_items:
        st.info("📊 Data Table Extracted from Voice:")
        df = pd.DataFrame(table_items, columns=["Category/Subject", "Value/Score"])
        st.table(df)

    # Sync button to send data to Firebase
    if st.button("📢 Publish to Students"):
        if db and current_notes:
            db.collection("session").document("live").set({
                "notes": current_notes,
                "table": dict(table_items),
                "active": True
            })
            st.success("Lecture synced to Student Portal!")

# --- 5. STUDENT PORTAL ---
else:
    st.header("👤 Student Portal")
    
    # Check if student has joined (Attendance)
    if 'verified' not in st.session_state:
        with st.form("Student_Attendance"):
            s_name = st.text_input("Full Name")
            s_roll = st.text_input("Roll Number")
            if st.form_submit_button("Join Class"):
                if s_name and s_roll and db:
                    # Save attendance record to Firestore
                    db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                    st.session_state.verified = True
                    st.session_state.student_name = s_name
                    st.rerun()
    else:
        st.success(f"Welcome, {st.session_state.student_name}!")
        
        # Multilingual Translation
        lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi"}
        target_lang = st.selectbox("Select Display Language:", list(lang_map.keys()))

        if db:
            # Fetch the latest lecture from Cloud
            live_ref = db.collection("session").document("live").get()
            if live_ref.exists:
                raw_text = live_ref.to_dict().get("notes", "Lecture in progress...")
                
                # Translation logic
                if target_lang != "English":
                    try:
                        translated = st.session_state.translator.translate(raw_text, dest=lang_map[target_lang]).text
                    except:
                        translated = raw_text
                else:
                    translated = raw_text

                st.info(f"**Lecture Notes ({target_lang}):**\n\n{translated}")
                
                # Audio Playback (TTS)
                if st.button("🔊 Read Aloud"):
                    tts = gTTS(text=translated, lang=lang_map[target_lang])
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp)

        st.divider()
        st.subheader("📂 Report Center")
        
        # PDF Generation for Students
        if st.button("Download Class Report (PDF)"):
            if db:
                current_data = db.collection("session").document("live").get().to_dict().get("notes", "No data")
                report_pdf = create_pdf("NeuralBridge Lecture Report", [current_data])
                st.download_button("Click to Save PDF", report_pdf, "Class_Report.pdf")
