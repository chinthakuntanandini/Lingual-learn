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

# --- 1. FIREBASE CONNECTION ENGINE ---
@st.cache_resource
def init_db():
    """Establishes connection to Firebase Firestore using Streamlit Secrets."""
    try:
        if "firebase" in st.secrets:
            # Load credentials from streamlit secrets
            info = dict(st.secrets["firebase"])
            # Essential: Strip extra spaces and ensure correct PEM format for the Private Key
            info["private_key"] = info["private_key"].strip().replace("\\n", "\n")
            
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        # If the PEM file or connection fails, show the error here
        st.error(f"Firebase Config Error: {e}")
    return None

db = init_db()

# Initialize Google Translator in Session State
if 'translator' not in st.session_state:
    st.session_state.translator = Translator()

# --- 2. UTILITY FUNCTIONS ---
def create_pdf(title, content_list):
    """Generates a PDF document from a list of strings."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for line in content_list:
        pdf.multi_cell(0, 10, txt=str(line))
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD (ADMIN) ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔊 Live Lecture Capture")
        # Records audio from browser microphone
        audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Process", key='teacher_mic')
        
        if audio:
            recognizer = sr.Recognizer()
            try:
                # Convert recorded bytes to an audio file object
                with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
                    audio_data = recognizer.record(source)
                    # Convert Voice to Text (English - India accent)
                    text = recognizer.recognize_google(audio_data, language='en-IN')
                    st.session_state.master_notes = text
                    st.success("Voice successfully converted to text!")
            except Exception as e:
                st.error("Audio processing failed. Please speak clearly.")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img_file = st.file_uploader("Upload Class Diagram", type=['jpg', 'png', 'jpeg'])
        if img_file:
            st.image(img_file, caption="Live Class Diagram", width=300)

    # Display and Edit the Transcript
    st.subheader("📝 Current Transcript")
    lecture_text = st.text_area("Review your lecture notes:", value=st.session_state.get('master_notes', ""), height=150)
    
    # --- TABLE EXTRACTION LOGIC ---
    # Automatically finds patterns like 'Maths: 90' or 'Rice: 50'
    table_items = re.findall(r"(\w+)\s*[:]\s*(\d+)", lecture_text)
    if table_items:
        st.info("📊 Data Table detected from voice!")
        df = pd.DataFrame(table_items, columns=["Item", "Value"])
        st.table(df)

    st.divider()
    
    # Sync with Firebase Cloud
    if st.button("📢 Sync & Publish to Students"):
        if db and lecture_text:
            db.collection("session").document("live").set({
                "notes": lecture_text,
                "table": dict(table_items),
                "active": True
            })
            st.success("Lecture shared with students via Cloud!")

# --- 5. STUDENT PORTAL (USER) ---
else:
    st.header("👤 Student Portal")
    
    # Attendance / Verification Logic
    if 'verified' not in st.session_state:
        with st.form("Student_Login"):
            s_name = st.text_input("Enter Your Full Name")
            s_roll = st.text_input("Enter Roll Number")
            if st.form_submit_button("Join Class"):
                if s_name and s_roll and db:
                    # Save attendance to Firebase
                    db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                    st.session_state.verified = True
                    st.session_state.student_name = s_name
                    st.rerun()
    else:
        st.success(f"Verified: {st.session_state.student_name}")
        
        # Translation Options
        lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi"}
        target_lang = st.selectbox("Translate Notes To:", list(lang_map.keys()))

        if db:
            # Fetch live data from Firestore
            live_ref = db.collection("session").document("live").get()
            if live_ref.exists:
                raw_text = live_ref.to_dict().get("notes", "")
                
                # Translation Engine
                if target_lang != "English":
                    try:
                        translated = st.session_state.translator.translate(raw_text, dest=lang_map[target_lang]).text
                    except:
                        translated = raw_text # Fallback to original if translation fails
                else:
                    translated = raw_text

                st.info(f"**Lecture Content ({target_lang}):**\n\n{translated}")
                
                # Voice Playback (Text-to-Speech)
                if st.button("🔊 Listen to Notes"):
                    tts = gTTS(text=translated, lang=lang_map[target_lang])
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp)

        st.divider()
        st.subheader("📥 Downloads")
        
        # Logic to generate PDF from Firebase data
        if st.button("Generate Report PDF"):
            if db:
                notes_data = db.collection("session").document("live").get().to_dict().get("notes", "Empty")
                pdf_bytes = create_pdf("NeuralBridge Lecture Summary", [notes_data])
                st.download_button("Click here to Download", pdf_bytes, "Lecture_Notes.pdf")
