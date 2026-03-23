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
translator = Translator()

# --- 2. PDF GENERATION ---
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

# --- 3. NAVIGATION ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔊 Capture Lecture")
        audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Sync", key='t_mic')
        if audio:
            recognizer = sr.Recognizer()
            try:
                with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
                    text = recognizer.recognize_google(recognizer.record(source))
                    st.session_state.master_notes = text
                    table_pairs = dict(re.findall(r"(\w+)\s*[:]\s*(\d+)", text))
                    if db:
                        db.collection("session").document("live").set({"notes": text, "table": table_pairs, "active": True})
                        st.success("Synced to Cloud!")
            except:
                st.error("Audio not clear. Try again.")

    with col2:
        st.subheader("🖼️ Diagram")
        img = st.file_uploader("Upload Image", type=['jpg', 'png'])
        if img: st.image(img, width=250)

    st.text_area("Live Transcript:", value=st.session_state.get('master_notes', ""), height=100)
    
    if st.button("📢 Publish Notes & Attendance"):
        if db:
            notes = st.session_state.get('master_notes', "No content")
            db.collection("delivery").document("notes").set({"ready": True, "data": notes})
            docs = db.collection("attendance").stream()
            att = [f"{d.to_dict()['Name']} ({d.to_dict()['Roll']})" for d in docs]
            db.collection("delivery").document("attendance").set({"ready": True, "list": att})
            st.success("Published to Students!")

# --- 5. STUDENT PORTAL ---
else:
    st.header("👤 Student Portal")
    if 'verified' not in st.session_state:
        with st.form("Login"):
            name, roll = st.text_input("Name"), st.text_input("Roll")
            if st.form_submit_button("Join Class") and name and roll:
                if db: db.collection("attendance").document(roll).set({"Name": name, "Roll": roll})
                st.session_state.verified, st.session_state.s_name = True, name
                st.rerun()
    else:
        st.success(f"Connected: {st.session_state.s_name}")
        lang = st.selectbox("Language:", ["English", "Telugu", "Hindi"])
        
        if db:
            live = db.collection("session").document("live").get()
            if live.exists:
                txt = live.to_dict().get("notes", "")
                disp = translator.translate(txt, dest=lang.lower()[:2]).text if lang != "English" else txt
                st.info(f"**Notes:** {disp}")
                if st.button("🔊 Listen"):
                    tts = gTTS(text=disp, lang=lang.lower()[:2])
                    fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp)

        st.divider()
        if db:
            n_ref = db.collection("delivery").document("notes").get()
            if n_ref.exists and n_ref.to_dict().get("ready"):
                st.download_button("📥 Class Notes (PDF)", create_pdf("Notes", [n_ref.to_dict()['data']]), "Notes.pdf")
            
            a_ref = db.collection("delivery").document("attendance").get()
            if a_ref.exists and a_ref.to_dict().get("ready"):
                st.download_button("📥 Attendance (PDF)", create_pdf("Attendance", a_ref.to_dict()['list']), "Attendance.pdf")
