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

# --- 1. FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"Firebase Config Error: {e}")
    return None

db = init_db()

# Translator initialize (Safe way to avoid connection errors)
if 'translator' not in st.session_state:
    st.session_state.translator = Translator()

# --- 2. PDF GENERATION ENGINE (Using FPDF) ---
def create_pdf(title, content_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for line in content_list:
        pdf.multi_cell(0, 10, txt=str(line))
    # Return as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI NAVIGATION & STYLING ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔊 Live Lecture Capture")
        # Mic recorder for teacher
        audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Process", key='teacher_mic')
        
        if audio:
            recognizer = sr.Recognizer()
            try:
                with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    st.session_state.master_notes = text
                    
                    # Logic for Table detection (e.g., "Maths: 90")
                    table_pairs = dict(re.findall(r"(\w+)\s*[:]\s*(\d+)", text))
                    
                    if db:
                        db.collection("session").document("live").set({
                            "notes": text,
                            "table": table_pairs,
                            "active": True
                        })
                        st.success("Lecture synced to Cloud!")
            except Exception as e:
                st.error("Audio processing failed. Please speak clearly.")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img_file = st.file_uploader("Upload Class Diagram", type=['jpg', 'png', 'jpeg'])
        if img_file:
            st.image(img_file, caption="Live Diagram", width=300)

    st.text_area("Current Transcript:", value=st.session_state.get('master_notes', ""), height=150)

    st.divider()
    st.subheader("📤 Post-Class Distribution")
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("📢 Publish Class Notes"):
            notes = st.session_state.get('master_notes', "No content recorded.")
            if db:
                db.collection("delivery").document("notes").set({"ready": True, "data": notes})
                st.success("Notes published for students!")

    with c2:
        if st.button("📝 Publish Attendance Report"):
            if db:
                docs = db.collection("attendance").stream()
                att_list = [f"{d.to_dict()['Name']} (Roll: {d.to_dict()['Roll']})" for d in docs]
                if att_list:
                    db.collection("delivery").document("attendance").set({"ready": True, "list": att_list})
                    st.success("Attendance PDF generated!")

# --- 5. STUDENT PORTAL ---
else:
    st.header("👤 Student Portal")
    
    # Login / Attendance
    if 'verified' not in st.session_state:
        with st.form("Student_Login"):
            s_name = st.text_input("Enter Your Full Name")
            s_roll = st.text_input("Enter Roll Number")
            if st.form_submit_button("Join Class"):
                if s_name and s_roll and db:
                    db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                    st.session_state.verified = True
                    st.session_state.student_name = s_name
                    st.rerun()
    else:
        st.success(f"Verified: {st.session_state.student_name}")
        
        # Multilingual Support
        lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi"}
        target_lang = st.selectbox("Select Language to View Notes:", list(lang_map.keys()))

        if db:
            live_ref = db.collection("session").document("live").get()
            if live_ref.exists:
                raw_text = live_ref.to_dict().get("notes", "")
                
                # Translation logic
                if target_lang != "English":
                    try:
                        translated = st.session_state.translator.translate(raw_text, dest=lang_map[target_lang]).text
                    except:
                        translated = raw_text # Fallback
                else:
                    translated = raw_text

                st.info(f"**Live Notes ({target_lang}):**\n\n{translated}")
                
                # Text-to-Speech (Audio Output)
                if st.button("🔊 Play Voice Note"):
                    tts = gTTS(text=translated, lang=lang_map[target_lang])
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp)

        st.divider()
        st.subheader("📂 Official Downloads")
        
        if db:
            # Download Notes
            n_ref = db.collection("delivery").document("notes").get()
            if n_ref.exists and n_ref.to_dict().get("ready"):
                n_pdf = create_pdf("Official Class Notes", [n_ref.to_dict()['data']])
                st.download_button("📥 Download Notes PDF", n_pdf, "Class_Notes.pdf")

            # Download Attendance
            a_ref = db.collection("delivery").document("attendance").get()
            if a_ref.exists and a_ref.to_dict().get("ready"):
                a_pdf = create_pdf("Final Attendance Sheet", a_ref.to_dict()['list'])
                st.download_button("📥 Download Attendance PDF", a_pdf, "Attendance_Sheet.pdf")
