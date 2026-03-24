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
import os

# --- 1. DATABASE CONNECTION (FIREBASE) ---
@st.cache_resource
def init_db():
    """Connects to Firestore. Handles the Private Key PEM format fix."""
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            # Clean the private key to prevent the 'InvalidByte' error
            key = info["private_key"].replace("\\n", "\n").strip().strip('"')
            info["private_key"] = key
            
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
    return None

db = init_db()

# Initialize Translator
if 'translator' not in st.session_state:
    st.session_state.translator = Translator()

# --- 2. MULTILINGUAL PDF LOGIC ---
def create_pdf(title, content, lang_code='en'):
    """Generates PDF using the .ttf fonts in your GitHub repo."""
    pdf = FPDF()
    pdf.add_page()
    
    # Path to fonts in your repository
    font_files = {
        "te": "NotoSansTelugu-Regular.ttf",
        "hi": "NotoSansDevanagari-Regular.ttf",
        "ta": "NotoSansTamil-Regular.ttf"
    }
    
    try:
        if lang_code in font_files and os.path.exists(font_files[lang_code]):
            # Loading your specific .ttf file for Unicode support
            pdf.add_font('CustomFont', '', font_files[lang_code], uni=True)
            pdf.set_font('CustomFont', '', 12)
        else:
            # Fallback to standard font if file is missing or language is English
            pdf.set_font("Arial", size=12)
    except:
        pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=str(content))
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- 3. PAGE CONFIGURATION ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔊 Live Lecture Capture")
        audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Process", key='teacher_mic')
        
        if audio:
            recognizer = sr.Recognizer()
            try:
                audio_file = io.BytesIO(audio['bytes'])
                with sr.AudioFile(audio_file) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)
                    # Voice to Text (English-India)
                    text = recognizer.recognize_google(audio_data, language='en-IN')
                    st.session_state.master_notes = text
                    st.success("Voice Captured!")
            except Exception as e:
                st.error(f"Audio processing failed: {e}")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img_file = st.file_uploader("Upload Class Diagram", type=['jpg', 'png', 'jpeg'])
        if img_file:
            st.image(img_file, caption="Live Diagram", width=300)

    st.divider()
    st.subheader("📝 Current Transcript")
    current_notes = st.text_area("Review Lecture Notes:", value=st.session_state.get('master_notes', ""), height=150)
    
    # --- AUTOMATIC TABLE GENERATION ---
    # Patterns like 'Math: 90' trigger a table
    table_data = re.findall(r"([\w\s]+)\s*[:]\s*(\d+)", current_notes)
    if table_data:
        st.info("📊 Data Table Detected:")
        df = pd.DataFrame(table_data, columns=["Item", "Value"])
        st.table(df)

    if st.button("📢 Publish to Students"):
        if db and current_notes:
            db.collection("session").document("live").set({
                "notes": current_notes,
                "table": dict(table_data),
                "active": True
            })
            st.success("Lecture synced to Cloud!")

# --- 5. STUDENT PORTAL ---
else:
    st.header("👤 Student Portal")
    
    if 'verified' not in st.session_state:
        with st.form("Student_Login"):
            s_name = st.text_input("Name")
            s_roll = st.text_input("Roll No")
            if st.form_submit_button("Join"):
                if s_name and s_roll and db:
                    db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                    st.session_state.verified = True
                    st.session_state.student_name = s_name
                    st.rerun()
    else:
        st.success(f"Verified: {st.session_state.student_name}")
        
        lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi"}
        target_lang = st.selectbox("Translate to:", list(lang_map.keys()))

        if db:
            live_ref = db.collection("session").document("live").get()
            if live_ref.exists:
                raw_text = live_ref.to_dict().get("notes", "")
                
                # Translation logic
                if target_lang != "English":
                    try:
                        translated = st.session_state.translator.translate(raw_text, dest=lang_map[target_lang]).text
                    except:
                        translated = raw_text
                else:
                    translated = raw_text

                st.info(f"**Lecture Notes ({target_lang}):**\n\n{translated}")
                
                if st.button("🔊 Read Aloud"):
                    with st.spinner("Generating Audio..."):
                        tts = gTTS(text=translated, lang=lang_map[target_lang])
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        st.audio(audio_fp)

        st.divider()
        if st.button("📥 Download PDF Report"):
            if db:
                notes = db.collection("session").document("live").get().to_dict().get("notes", "")
                pdf_bytes = create_pdf("NeuralBridge Report", notes, lang_code=lang_map[target_lang])
                st.download_button("Download Now", pdf_bytes, "Lecture_Notes.pdf")
