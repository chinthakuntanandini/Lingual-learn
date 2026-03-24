import io
import os
import re

import pandas as pd
import speech_recognition as sr
import streamlit as st
from fpdf import FPDF
from google.cloud import firestore
from google.oauth2 import service_account
from googletrans import Translator
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder


# --- 1. DATABASE CONNECTION (FIREBASE) ---
@st.cache_resource
def init_db():
    """Connect to Firestore with safe private key normalization."""
    try:
        info = None

        # 1) Streamlit secrets (Cloud / local secrets.toml)
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])

        # 2) Optional local key.json fallback
        elif os.path.exists("key.json"):
            import json

            with open("key.json", "r", encoding="utf-8") as f:
                info = json.load(f)

        if not info:
            st.error("Firebase config not found. Add [firebase] in st.secrets or provide key.json.")
            return None

        # Normalize private key to avoid InvalidByte / PEM parse errors
        raw_key = str(info.get("private_key", ""))
        cleaned_key = raw_key.strip().strip('"').strip("'")
        cleaned_key = cleaned_key.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
        info["private_key"] = cleaned_key

        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds, project=info["project_id"])

    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        return None


db = init_db()

# Initialize Translator once
if "translator" not in st.session_state:
    st.session_state.translator = Translator()

if "master_notes" not in st.session_state:
    st.session_state.master_notes = ""


# --- 2. MULTILINGUAL PDF LOGIC ---
def create_pdf(title, content, lang_code="en"):
    """Generate PDF. Uses Unicode fonts for Telugu/Hindi/Tamil if available."""
    pdf = FPDF()
    pdf.add_page()

    font_files = {
        "te": "NotoSansTelugu-Regular.ttf",
        "hi": "NotoSansDevanagari-Regular.ttf",
        "ta": "NotoSansTamil-Regular.ttf",
    }

    try:
        if lang_code in font_files and os.path.exists(font_files[lang_code]):
            pdf.add_font("CustomFont", "", font_files[lang_code], uni=True)
            pdf.set_font("CustomFont", "", 12)
        else:
            pdf.set_font("Arial", size=12)
    except Exception:
        pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, txt=title, ln=1, align="C")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=str(content))

    return pdf.output(dest="S").encode("latin-1", errors="replace")


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
        audio = mic_recorder(
            start_prompt="▶️ Start Recording",
            stop_prompt="🛑 Stop & Process",
            key="teacher_mic",
        )

        if audio:
            recognizer = sr.Recognizer()
            try:
                audio_file = io.BytesIO(audio["bytes"])
                with sr.AudioFile(audio_file) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="en-IN")
                st.session_state.master_notes = text
                st.success("Voice Captured!")
            except Exception as e:
                st.error(f"Audio processing failed: {e}")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img_file = st.file_uploader("Upload Class Diagram", type=["jpg", "png", "jpeg"])
        if img_file:
            st.image(img_file, caption="Live Diagram", width=300)

    st.divider()
    st.subheader("📝 Current Transcript")
    current_notes = st.text_area(
        "Review Lecture Notes:",
        value=st.session_state.get("master_notes", ""),
        height=180,
    )

    # Automatic table extraction: e.g., "Math: 90"
    table_data = re.findall(r"([\w\s]+)\s*[:]\s*(\d+)", current_notes)
    if table_data:
        st.info("📊 Data Table Detected:")
        df = pd.DataFrame(table_data, columns=["Item", "Value"])
        st.table(df)

    if st.button("📢 Publish to Students"):
        if not db:
            st.error("Database not connected.")
        elif not current_notes.strip():
            st.warning("No lecture notes to publish.")
        else:
            try:
                db.collection("session").document("live").set(
                    {
                        "notes": current_notes,
                        "table": dict(table_data) if table_data else {},
                        "active": True,
                    }
                )
                st.success("Lecture synced to Cloud!")
            except Exception as e:
                st.error(f"Publish failed: {e}")


# --- 5. STUDENT PORTAL ---
else:
    st.header("👤 Student Portal")

    if "verified" not in st.session_state:
        with st.form("Student_Login"):
            s_name = st.text_input("Name")
            s_roll = st.text_input("Roll No")
            joined = st.form_submit_button("Join")

            if joined:
                if not db:
                    st.error("Database not connected.")
                elif s_name and s_roll:
                    try:
                        db.collection("attendance").document(s_roll).set(
                            {"Name": s_name, "Roll": s_roll}
                        )
                        st.session_state.verified = True
                        st.session_state.student_name = s_name
                        st.rerun()
                    except Exception as e:
                        st.error(f"Join failed: {e}")
                else:
                    st.warning("Please enter Name and Roll No.")
    else:
        st.success(f"Verified: {st.session_state.student_name}")

        lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta"}
        target_lang_name = st.selectbox("Translate to:", list(lang_map.keys()))
        target_lang_code = lang_map[target_lang_name]

        raw_text = ""
        translated = ""

        if db:
            try:
                live_ref = db.collection("session").document("live").get()
                if live_ref.exists:
                    raw_text = live_ref.to_dict().get("notes", "")
                else:
                    st.info("No live lecture published yet.")
            except Exception as e:
                st.error(f"Failed to fetch lecture: {e}")

        if raw_text:
            if target_lang_code != "en":
                try:
                    translated = st.session_state.translator.translate(
                        raw_text, dest=target_lang_code
                    ).text
                except Exception:
                    translated = raw_text
            else:
                translated = raw_text

            st.info(f"**Lecture Notes ({target_lang_name}):**\n\n{translated}")

            if st.button("🔊 Read Aloud"):
                try:
                    with st.spinner("Generating Audio..."):
                        tts = gTTS(text=translated, lang=target_lang_code)
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        audio_fp.seek(0)
                        st.audio(audio_fp, format="audio/mp3")
                except Exception as e:
                    st.error(f"TTS failed: {e}")

            st.divider()
            if st.button("📥 Download PDF Report"):
                try:
                    pdf_bytes = create_pdf(
                        "NeuralBridge Report",
                        translated if translated else raw_text,
                        lang_code=target_lang_code,
                    )
                    st.download_button(
                        "Download Now",
                        data=pdf_bytes,
                        file_name="Lecture_Notes.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")
