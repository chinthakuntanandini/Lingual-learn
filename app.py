import io
import json
import os
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from fpdf import FPDF
from google.cloud import firestore
from google.oauth2 import service_account
from googletrans import Translator
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr


def _normalize_private_key(raw_key: str) -> str:
    key = (raw_key or "").strip().strip('"').strip("'")
    key = key.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    # Trim accidental leading/trailing spaces per line.
    key = "\n".join(line.strip() for line in key.split("\n"))
    return key


@st.cache_resource
def init_db():
    """Connect to Firestore with robust key handling."""
    info = None
    source = "none"
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            source = "st.secrets"
        elif os.path.exists("key.json"):
            with open("key.json", "r", encoding="utf-8") as f:
                info = json.load(f)
            source = "key.json"

        if not info:
            st.error("Firebase config missing. Add [firebase] in secrets or key.json.")
            return None

        info["private_key"] = _normalize_private_key(info.get("private_key", ""))

        # Quick validation before creating credentials.
        key = info.get("private_key", "")
        if not key.startswith("-----BEGIN PRIVATE KEY-----"):
            st.error(f"Firebase key format invalid from {source}: missing BEGIN marker.")
            return None
        if "-----END PRIVATE KEY-----" not in key:
            st.error(f"Firebase key format invalid from {source}: missing END marker.")
            return None

        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error ({source}): {e}")
        return None


def create_pdf(title, content, lang_code="en"):
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


st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

db = init_db()
if "translator" not in st.session_state:
    st.session_state.translator = Translator()
if "master_notes" not in st.session_state:
    st.session_state.master_notes = ""


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
        height=150,
    )

    table_data = re.findall(r"([\w\s]+)\s*[:]\s*(\d+)", current_notes)
    if table_data:
        st.info("📊 Data Table Detected:")
        df = pd.DataFrame(table_data, columns=["Item", "Value"])
        st.table(df)

    if st.button("📢 Publish to Students"):
        if db and current_notes.strip():
            try:
                db.collection("session").document("live").set(
                    {
                        "notes": current_notes,
                        "table": dict(table_data),
                        "active": True,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                st.success("Lecture synced to Cloud!")
                st.rerun()
            except Exception as e:
                st.error(f"Publish failed: {e}")
        elif not db:
            st.error("Database is not connected.")
        else:
            st.warning("Please enter notes before publishing.")

    st.divider()
    st.subheader("👥 Live Attendance (Joined Students)")
    if db:
        try:
            attendance_docs = db.collection("attendance").stream()
            attendance_rows = []
            for doc in attendance_docs:
                data = doc.to_dict() or {}
                attendance_rows.append(
                    {
                        "Roll No": data.get("Roll", doc.id),
                        "Name": data.get("Name", "N/A"),
                    }
                )

            if attendance_rows:
                att_df = pd.DataFrame(attendance_rows).drop_duplicates(subset=["Roll No"], keep="last")
                st.dataframe(att_df, use_container_width=True)
                st.success(f"Total Present: {len(att_df)}")
            else:
                st.info("No students joined yet.")
        except Exception as e:
            st.error(f"Failed to load attendance: {e}")
    else:
        st.error("Database is not connected.")

else:
    st.header("👤 Student Portal")
    if "verified" not in st.session_state:
        with st.form("Student_Login"):
            s_name = st.text_input("Name")
            s_roll = st.text_input("Roll No")
            submitted = st.form_submit_button("Join")
            if submitted:
                if s_name and s_roll and db:
                    db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                    st.session_state.verified = True
                    st.session_state.student_name = s_name
                    st.rerun()
                elif not db:
                    st.error("Database is not connected.")
    else:
        st.success(f"Verified: {st.session_state.student_name}")
        lang_map = {"English": "en","Telugu": "te",  "Urdu": "ur", "Hindi": "hi",}
        target_lang = st.selectbox("Translate to:", list(lang_map.keys()))
        target_code = lang_map[target_lang]
        st.button("🔄 Refresh Live Notes")

        translated = ""
        if db:
            try:
                live_ref = db.collection("session").document("live").get()
                if live_ref.exists:
                    payload = live_ref.to_dict() or {}
                    raw_text = payload.get("notes", "")
                    is_active = payload.get("active", False)
                    updated_at = payload.get("updated_at", "N/A")

                    if is_active and raw_text.strip():
                        if target_lang != "English":
                            try:
                                translated = st.session_state.translator.translate(raw_text, dest=target_code).text
                            except Exception:
                                translated = raw_text
                        else:
                            translated = raw_text

                        st.caption(f"Last updated: {updated_at}")
                        st.info(f"**Lecture Notes ({target_lang}):**\n\n{translated}")

                        if st.button("🔊 Read Aloud"):
                            with st.spinner("Generating Audio..."):
                                tts = gTTS(text=translated, lang=target_code)
                                audio_fp = io.BytesIO()
                                tts.write_to_fp(audio_fp)
                                audio_fp.seek(0)
                                st.audio(audio_fp, format="audio/mp3")
                    else:
                        st.info("No live lecture published yet.")
                else:
                    st.info("No live lecture published yet.")
            except Exception as e:
                st.error(f"Failed to load live notes: {e}")

        st.divider()
        if st.button("📥 Download PDF Report"):
            if db:
                notes_doc = db.collection("session").document("live").get()
                notes = notes_doc.to_dict().get("notes", "") if notes_doc.exists else ""
                pdf_bytes = create_pdf("NeuralBridge Report", notes, lang_code=target_code)
                st.download_button("Download Now", pdf_bytes, "Lecture_Notes.pdf", mime="application/pdf")
