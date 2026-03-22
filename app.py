import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os
from fpdf import FPDF
import pandas as pd
import speech_recognition as sr
from google.cloud import firestore
from google.oauth2 import service_account

# --- 1. FIREBASE CONNECTION (Securely using Streamlit Secrets) ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            st.error("Firebase secrets not found! Please add them in App Settings > Secrets.")
            return None
            
        firebase_info = dict(st.secrets["firebase"])
        # Fix for private key format issues in Cloud
        raw_key = firebase_info["private_key"]
        private_key = raw_key.replace("\\n", "\n").strip().strip('"')
        firebase_info["private_key"] = private_key

        creds = service_account.Credentials.from_service_account_info(firebase_info)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        return None

db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", page_icon="🎓", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: AI Smart Classroom")
st.markdown("---")

# Language Mappings
lang_options = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Urdu": "ur"}
lang_map = {v: k for k, v in lang_options.items()}

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("👤 Student Registration")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
        roll = st.text_input("Roll Number / ID")
    with col2:
        lang_display = st.selectbox("Select Your Native Language", list(lang_options.keys()))
        lang_code = lang_options[lang_display]

    if st.button("Join Class"):
        if db and name and roll:
            db.collection("requests").document(roll).set({
                "name": name,
                "roll": roll,
                "language": lang_code,
                "status": "pending"
            })
            st.success(f"Registration Successful! {name}, wait for teacher's approval.")
        else:
            st.warning("Please fill all the details.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Approval Panel")
    if db:
        requests = db.collection("requests").where("status", "==", "pending").stream()
        found = False
        for doc in requests:
            found = True
            data = doc.to_dict()
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.info(f"**Student:** {data['name']} | **ID:** {data['roll']} | **Lang:** {lang_map.get(data['language'])}")
            with col_b:
                if st.button("Approve", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
        if not found:
            st.write("No pending requests at the moment.")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("🎤 Real-time Multilingual Session")
    
    # Teacher Input: Audio File Upload
    st.subheader("Step 1: Upload Lesson Audio")
    uploaded_file = st.file_uploader("Upload Audio (.wav format)", type=["wav"])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(uploaded_file.read())
            temp_path = temp_audio.name

        r = sr.Recognizer()
        try:
            with sr.AudioFile(temp_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                st.session_state.class_content = text
                st.success("Audio Processed Successfully!")
                st.markdown(f"> **Recognized Text:** {text}")
        except Exception as e:
            st.error(f"Speech Recognition Error: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    st.markdown("---")
    
    # Processing for Students
    st.subheader("Step 2: Student Translations & Audio")
    students = []
    if db:
        approved = db.collection("requests").where("status", "==", "approved").stream()
        for doc in approved:
            students.append(doc.to_dict())
    
    if "class_content" in st.session_state and students:
        for stu in students:
            with st.expander(f"Student: {stu['name']} ({lang_map[stu['language']]})"):
                try:
                    # Translation logic
                    translated_text = GoogleTranslator(source='auto', target=stu["language"]).translate(st.session_state.class_content)
                    st.write(f"**Translation:** {translated_text}")
                    
                    # Voice conversion
                    tts = gTTS(translated_text, lang=stu["language"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name)
                except Exception as e:
                    st.error(f"Error processing for {stu['name']}: {e}")

        # PDF Download for Lesson Notes
        if st.button("Generate Lesson Report (PDF)"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=14)
            pdf.cell(200, 10, txt="NeuralBridge - Class Notes", ln=1, align='C')
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt=f"\nOriginal Lesson:\n{st.session_state.class_content}")
            pdf.output("report.pdf")
            with open("report.pdf", "rb") as f:
                st.download_button("Download PDF", f, file_name="Lesson_Notes.pdf")
    else:
        st.info("Wait for audio upload or student approvals to begin.")
