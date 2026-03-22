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

# --- 1. FIREBASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            st.error("Firebase secrets not found in Streamlit Cloud settings!")
            return None
            
        firebase_info = dict(st.secrets["firebase"])
        # Fix for private key newline characters
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
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: AI Smart Classroom")

# Language Mappings
lang_options = {"Telugu": "te", "Urdu": "ur", "English": "en", "Hindi": "hi", "Tamil": "ta"}
lang_map = {v: k for k, v in lang_options.items()}

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Name")
    roll = st.text_input("Enter Roll Number")
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
            st.success(f"Request sent! {name}, please wait for Teacher's approval.")
        else:
            st.warning("Please provide all details.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    if db:
        requests = db.collection("requests").where("status", "==", "pending").stream()
        found = False
        for doc in requests:
            found = True
            data = doc.to_dict()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{data['name']}** ({data['roll']}) - Lang: {lang_map.get(data['language'], 'Unknown')}")
            with col2:
                if st.button("Approve", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
        if not found:
            st.info("No pending join requests.")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("🎤 Live Session (Voice Enabled)")
    
    uploaded_file = st.file_uploader("Upload Teacher's Voice (.wav)", type=["wav"])
    
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
                st.success("Speech recognized successfully!")
                st.info(f"📚 Original Lesson (English): {text}")
        except Exception as e:
            st.error(f"Audio processing error: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    st.markdown("---")
    
    students = []
    if db:
        approved = db.collection("requests").where("status", "==", "approved").stream()
        for doc in approved:
            students.append(doc.to_dict())
    
    if "class_content" in st.session_state and students:
        st.subheader("🌐 Multilingual Translation & Audio")
        
        for stu in students:
            try:
                # Using Deep Translator for better stability on Streamlit Cloud
                translated_text = GoogleTranslator(source='auto', target=stu["language"]).translate(st.session_state.class_content)
                
                st.write(f"🔔 **For {stu['name']} ({lang_map[stu['language']]}):**")
                st.success(translated_text)
                
                tts = gTTS(translated_text, lang=stu["language"])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.
