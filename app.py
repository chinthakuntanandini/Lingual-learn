import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os
import pandas as pd
import speech_recognition as sr
from google.cloud import firestore
from google.oauth2 import service_account

# --- FIREBASE ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            return None
        firebase_info = dict(st.secrets["firebase"])
        raw_key = firebase_info["private_key"]
        private_key = raw_key.replace("\\n", "\n").strip().strip('"')
        firebase_info["private_key"] = private_key
        creds = service_account.Credentials.from_service_account_info(firebase_info)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except:
        return None

db = init_connection()

st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.title("🎓 NeuralBridge: Smart Classroom")

page = st.sidebar.selectbox("Menu", ["Student Join", "Teacher Dashboard", "Live Class"])
lang_options = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}

if page == "Student Join":
    name = st.text_input("Name")
    roll = st.text_input("Roll No")
    lang = st.selectbox("Language", list(lang_options.keys()))
    if st.button("Join"):
        if db and name and roll:
            db.collection("requests").document(roll).set({"name": name, "roll": roll, "language": lang_options[lang], "status": "pending"})
            st.success("Joined!")

elif page == "Teacher Dashboard":
    if db:
        docs = db.collection("requests").where("status", "==", "pending").stream()
        for doc in docs:
            d = doc.to_dict()
            st.write(f"{d['name']} ({d['roll']})")
            if st.button("Approve", key=doc.id):
                db.collection("requests").document(doc.id).update({"status": "approved"})
                st.rerun()

elif page == "Live Class":
    up = st.file_uploader("Upload Voice (.wav)", type=["wav"])
    if up:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(up.read())
            path = f.name
        r = sr.Recognizer()
        with sr.AudioFile(path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio)
            st.info(f"Original: {text}")
            
            # Show for all approved students
            approved = db.collection("requests").where("status", "==", "approved").stream()
            for s in approved:
                sd = s.to_dict()
                trans = GoogleTranslator(source='auto', target=sd["language"]).translate(text)
                st.success(f"{sd['name']} ({sd['language']}): {trans}")
                tts = gTTS(trans, lang=sd["language"])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as af:
                    tts.save(af.name)
                    st.audio(af.name)
