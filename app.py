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
        # Streamlit Secrets nundi Firebase details tiskuntundi
        info = dict(st.secrets["firebase"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        return None

db = init_db()
translator = Translator()

# --- 2. PDF GENERATION ENGINE ---
def create_pdf(title, content_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for line in content_list:
        pdf.multi_cell(0, 10, txt=str(line))
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI NAVIGATION ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔊 Capture Lecture & Table")
        audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Sync", key='teacher_mic')
        
        if audio:
            recognizer = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
                text = recognizer.recognize_google(recognizer.record(source))
                st.session_state.master_notes = text
                
                # Logic for Table (Ex: "Student: 90, Marks: 80")
                table_pairs = re.findall(r"(\w+)\s*[:]\s*(\d+)", text)
                table_dict = dict(table_pairs) if table_pairs else {}
                
                # Sync to Cloud
                if db:
                    db.collection("session").document("live").set({
                        "notes": text,
                        "table": table_dict,
                        "active": True
                    })
                    st.success("Lecture & Table Synced!")

    with col2:
        st.subheader("🖼️ Diagram Upload")
        img = st.file_uploader("Upload Diagram (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
        if img:
            st.image(img, caption="Current Class Diagram", width=300)

    st.text_area("Live Transcript:", value=st.session_state.get('master_notes', ""), height=100)

    st.divider()

    st.subheader("📤 Post-Class Distribution")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📢 Publish Class Notes PDF"):
            content = st.session_state.get('master_notes', "No content recorded.")
            if db:
                db.collection("delivery").document("notes").set({"ready": True, "data": content})
                st.success("Notes PDF sent to Students!")

    with c2:
        if st.button("📝 Publish Attendance PDF"):
            if db:
                docs = db.collection("attendance").stream()
                att_list = [f"{d.to_dict()['Name']} (Roll: {d.to_dict()['Roll']})" for d in docs]
                if att_list:
                    db.collection("delivery").document("attendance").set({"ready": True, "list": att_list})
                    st.success("Attendance PDF sent to Students!")

# --- 5. STUDENT PORTAL ---
elif choice == "Student Portal":
    st.header("👤 Student Portal")
    
    # Entrance & Attendance
    if 'verified' not in st.session_state:
        with st.form("Student_Login"):
            s_name = st.text_input("Full Name")
            s_roll = st.text_input("Roll Number")
            if st.form_submit_button("Join Class"):
                if s_name and s_roll and db:
                    db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                    st.session_state.verified = True
                    st.session_state.student_name = s_name
                    st.rerun()
    else:
        st.success(f"Welcome to Live Class, {st.session_state.student_name}!")
        
        # Language Selection for View
        lang_opt = {"English": "en", "Telugu": "te", "Hindi": "hi"}
        sel_lang = st.selectbox("Select View Language:", list(lang_opt.keys()))

        # Display Live Data
        if db:
            live_ref = db.collection("session").document("live").get()
            if live_ref.exists:
                raw_text = live_ref.to_dict().get("notes", "")
                # Translation for View
                disp_text = translator.translate(raw_text, dest=lang_opt[sel_lang]).text if sel_lang != "English" else raw_text
                
                st.info(f"**Live Notes ({sel_lang}):**\n{disp_text}")
                
                if st.button("🔊 Play Voice"):
                    tts = gTTS(text=disp_text, lang=lang_opt[sel_lang])
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp)

        st.divider()
        st.subheader("📂 Download Official Documents (English)")

        if db:
            # Download Notes PDF
            n_ref = db.collection("delivery").document("notes").get()
            if n_ref.exists and n_ref.to_dict().get("ready"):
                n_pdf = create_pdf("Official Class Notes", [n_ref.to_dict()['data']])
                st.download_button("📥 Download Class Notes PDF", data=n_pdf, file_name="Class_Notes.pdf")

            # Download Attendance PDF
            a_ref = db.collection("delivery").document("attendance").get()
            if a_ref.exists and a_ref.to_dict().get("ready"):
                a_pdf = create_pdf("Final Attendance Report", a_ref.to_dict()['list'])
                st.download_button("📥 Download Attendance PDF", data=a_pdf, file_name="Attendance.pdf")
