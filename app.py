import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from googletrans import Translator
import io
import pydub
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Firebase Configuration using Streamlit Secrets ---
# We are now using the data from the Secrets tab instead of a local file.
if not firebase_admin._apps:
    try:
        # Fetching the secret key dictionary from Streamlit settings
        # Ensure you have [firebase_key] set up in your Streamlit Cloud Secrets!
        key_dict = dict(st.secrets["firebase_key"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        st.info("Check your Streamlit Cloud Secrets tab for the [firebase_key] configuration.")

db = firestore.client()

# --- 2. Page Setup ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

# Language codes for Speech Recognition and Translation
languages = {
    "English": {"speech": "en-US", "trans": "en"},
    "Telugu": {"speech": "te-IN", "trans": "te"},
    "Urdu": {"speech": "ur-PK", "trans": "ur"}
}

# --- 3. Sidebar Configuration ---
st.sidebar.header("Classroom Settings")
role = st.sidebar.selectbox("Select Role:", ["Teacher", "Student"])
fdp_lang = st.sidebar.selectbox("Teacher Language:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Language:", list(languages.keys()))

translator = Translator()
recognizer = sr.Recognizer()

# --- 4. Teacher Interface ---
if role == "Teacher":
    st.subheader("Teacher Dashboard (Source Input)")
    st.info(f"Broadcast Mode: Recording in {fdp_lang}")

    # Recording Component
    audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='live_mic')

    if audio_data:
        try:
            # Process Audio Data
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                # Speech to Text conversion
                original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])

                # Translate to Student's preferred language
                translated_res = translator.translate(original_text, dest=languages[std_lang]["trans"])
                translated_text = translated_res.text

                # Update Cloud Database (Firebase Firestore)
                db.collection("classroom").document("live_lecture").set({
                    "original": original_text,
                    "translated": translated_text,
                    "target_lang": std_lang,
                    "is_active": True
                })

                st.success(f"Original: {original_text}")
                st.success(f"Translated & Sent: {translated_text}")

        except Exception as e:
            st.error(f"Processing Error: {e}")

# --- 5. Student Interface ---
else:
    st.subheader("Student Dashboard (Live Output)")
    st.warning("Listening for teacher's live updates...")

    # Fetch latest data from Firestore
    doc_ref = db.collection("classroom").document("live_lecture")
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        # Visual output for the student
        st.markdown(f"### 📖 Live Translation ({std_lang}):")
        st.write(data.get('translated', 'No text found.'))
    else:
        st.info("The teacher hasn't started the lecture yet.")

    # Refresh button to fetch latest updates from Cloud
    if st.button("🔄 Sync with Teacher"):
        st.rerun()
