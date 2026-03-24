import io
import json
import os
import re
import base64
import tempfile
from datetime import datetime, timezone
from typing import List, Tuple

import pandas as pd
import streamlit as st
from fpdf import FPDF
from google.cloud import firestore
from google.oauth2 import service_account
from googletrans import Translator
from gtts import gTTS
import speech_recognition as sr


def _normalize_private_key(raw_key: str) -> str:
    key = (raw_key or "").strip().strip('"').strip("'")
    key = key.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    # Trim accidental leading/trailing spaces per line.
    key = "\n".join(line.strip() for line in key.split("\n"))
    return key


def extract_table_rows(notes: str) -> List[Tuple[str, str]]:
    """
    Extract simple table rows from free-form notes.
    Supports:
      - Key: Value
      - Key - Value
      - Key = Value
    """
    rows = []
    if not notes:
        return rows

    for raw_line in notes.splitlines():
        line = raw_line.strip(" -•\t")
        if not line:
            continue
        match = re.match(r"^([A-Za-z][\w\s()/]{1,60})\s*[:=\-]\s*(.+)$", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            rows.append((key, value))
    return rows


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


def create_pdf(title, content, lang_code="en", table_data=None, diagram_bytes=None, diagram_ext="png"):
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

    if table_data:
        pdf.ln(5)
        pdf.set_font_size(11)
        pdf.multi_cell(0, 8, txt="Table Data (English):")
        for key, value in table_data.items():
            pdf.multi_cell(0, 8, txt=f"- {key}: {value}")

    if diagram_bytes:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{diagram_ext}") as tmp:
                tmp.write(diagram_bytes)
                img_path = tmp.name
            pdf.ln(5)
            pdf.multi_cell(0, 8, txt="Class Diagram:")
            pdf.image(img_path, x=10, w=180)
            os.unlink(img_path)
        except Exception:
            pdf.multi_cell(0, 8, txt="Diagram could not be embedded in PDF.")

    return pdf.output(dest="S").encode("latin-1", errors="replace")


st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

db = init_db()
if "translator" not in st.session_state:
    st.session_state.translator = Translator()
if "master_notes" not in st.session_state:
    st.session_state.master_notes = ""
if "diagram_payload" not in st.session_state:
    st.session_state.diagram_payload = {}
if "student_tts_cache" not in st.session_state:
    st.session_state.student_tts_cache = {}


if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔊 Live Lecture Capture")
        st.caption("Stable mode: use WAV audio input (browser mic/file).")
        speech_lang_map = {
            "English (India)": "en-IN",
            "Telugu": "te-IN",
            "Hindi": "hi-IN",
            "Tamil": "ta-IN",
        }
        speech_lang = st.selectbox("Lecture Voice Language", list(speech_lang_map.keys()), index=1)
        wav_audio = st.audio_input("Record/Upload Lecture Audio (WAV)")

        if wav_audio:
            recognizer = sr.Recognizer()
            try:
                audio_file = io.BytesIO(wav_audio.getvalue())
                with sr.AudioFile(audio_file) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language=speech_lang_map[speech_lang])
                st.session_state.master_notes = text
                st.success("Voice Captured!")
            except Exception as e:
                st.error(f"Audio processing failed: {e}")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img_file = st.file_uploader("Upload Class Diagram", type=["jpg", "png", "jpeg"])
        if img_file:
            st.image(img_file, caption="Live Diagram", width=300)
            ext = "png" if img_file.type == "image/png" else "jpg"
            st.session_state.diagram_payload = {
                "data_b64": base64.b64encode(img_file.getvalue()).decode("utf-8"),
                "ext": ext,
            }

    st.divider()
    st.subheader("📝 Current Transcript")
    current_notes = st.text_area(
        "Review Lecture Notes:",
        value=st.session_state.get("master_notes", ""),
        height=150,
    )

    table_data = extract_table_rows(current_notes)
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
                        "diagram": st.session_state.get("diagram_payload", {}),
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
        lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta"}
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

                        # Auto-generate and autoplay audio for the selected language.
                        tts_cache_key = f"{target_code}::{translated}"
                        if tts_cache_key not in st.session_state.student_tts_cache:
                            with st.spinner("Generating Audio..."):
                                tts = gTTS(text=translated, lang=target_code)
                                audio_fp = io.BytesIO()
                                tts.write_to_fp(audio_fp)
                                st.session_state.student_tts_cache[tts_cache_key] = audio_fp.getvalue()

                        st.audio(
                            st.session_state.student_tts_cache[tts_cache_key],
                            format="audio/mp3",
                            autoplay=True,
                        )

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
                payload = notes_doc.to_dict() if notes_doc.exists else {}
                notes = payload.get("notes", "")
                table_payload = payload.get("table", {}) or {}
                diagram_payload = payload.get("diagram", {}) or {}

                # Keep lecture notes in selected language; table/diagram labels remain English.
                notes_for_pdf = notes
                if target_lang != "English" and notes.strip():
                    try:
                        notes_for_pdf = st.session_state.translator.translate(notes, dest=target_code).text
                    except Exception:
                        notes_for_pdf = notes

                diagram_bytes = None
                diagram_ext = diagram_payload.get("ext", "png")
                if diagram_payload.get("data_b64"):
                    try:
                        diagram_bytes = base64.b64decode(diagram_payload["data_b64"])
                    except Exception:
                        diagram_bytes = None

                pdf_bytes = create_pdf(
                    "NeuralBridge Report",
                    notes_for_pdf,
                    lang_code=target_code,
                    table_data=table_payload,
                    diagram_bytes=diagram_bytes,
                    diagram_ext=diagram_ext,
                )
                st.download_button("Download Now", pdf_bytes, "Lecture_Notes.pdf", mime="application/pdf")
