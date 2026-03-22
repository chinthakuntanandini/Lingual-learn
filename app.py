import streamlit as st
from googletrans import Translator
from gtts import gTTS
import tempfile
import os
from fpdf import FPDF
import pandas as pd
import speech_recognition as sr
from google.cloud import firestore
from google.oauth2 import service_account

# Initialize Translator
translator = Translator()

# ---------------- FIREBASE CONNECTION ----------------
@st.cache_resource
def init_connection():
    try:
        firebase_info = st.secrets["firebase"]
        # Essential Fix: Replace literal \n with actual newline for the PEM key
        private_key = firebase_info["private_key"].replace("\\n", "\n")

        creds_dict = dict(firebase_info)
        creds_dict["private_key"] = private_key

        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

db = init_connection()

# ---------------- UI SETTINGS ----------------
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])
st.title("🎓 NeuralBridge: AI Smart Classroom")

# Language Mappings
lang_options = {"Telugu": "te", "Urdu": "ur", "English": "en"}
lang_map = {"te": "Telugu", "ur": "Urdu", "en": "English"}

# ---------------- STUDENT JOIN PAGE ----------------
if page == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Name")
    roll = st.text_input("Enter Roll Number")
    # Fix: Corrected how selectbox handles dictionaries
    lang_display = st.selectbox("Select Language", list(lang_options.keys()))
    lang_code = lang_options[lang_display]

    if st.button("Join"):
        if db and name and roll:
            try:
                db.collection("requests").document(roll).set({
                    "name": name,
                    "roll": roll,
                    "language": lang_code,
                    "status": "pending"
                })
                st.success("Request Sent to Teacher! Please wait for approval.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter all details and ensure DB is connected.")

# ---------------- TEACHER DASHBOARD ----------------
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
                st.write(f"**{data['name']}** ({data['roll']}) - {lang_map.get(data['language'], 'Unknown')}")
            with col2:
                if st.button("Approve", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
        if not found:
            st.info("No pending requests at the moment.")

# ---------------- LIVE CLASS PAGE ----------------
elif page == "Live Class":
    st.header("🎤 Teacher Voice Enabled Class (Upload .wav)")

    uploaded_file = st.file_uploader("Upload Teacher Voice (.wav)", type=["wav"])
    
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
                st.success("Voice converted to text successfully!")
                st.info(f"📚 Recognized Text: {text}")
        except Exception as e:
            st.error(f"Could not recognize audio: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    st.markdown("---")
    st.subheader("👨‍🎓 Approved Students")
    
    students = []
    if db:
        approved = db.collection("requests").where("status", "==", "approved").stream()
        for doc in approved:
            data = doc.to_dict()
            students.append(data)
            st.write(f"✅ {data['name']} ({lang_map.get(data['language'], 'Unknown')})")
    
    if not students:
        st.warning("No students approved yet.")

    st.markdown("---")

    if "class_content" in st.session_state and students:
        st.subheader("🌐 Real-time Translation & Audio")
        
        for stu in students:
            try:
                translated = translator.translate(st.session_state.class_content, dest=stu["language"])
                st.write(f"**{stu['name']}** ({lang_map[stu['language']]}): {translated.text}")
                
                # Audio generation
                tts = gTTS(translated.text, lang=stu["language"])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.name)
                    st.audio(fp.name)
            except Exception as e:
                st.error(f"Translation/Audio Error for {stu['name']}: {e}")

        # --- Statistics ---
        st.subheader("📊 Class Overview")
        df = pd.DataFrame({
            "Metric": ["Original Text", "Total Students", "Languages"],
            "Value": [st.session_state.class_content[:50] + "...", len(students), ", ".join(set([lang_map[s["language"]] for s in students]))]
        })
        st.table(df)

        # --- Download Section ---
        st.subheader("📄 Reports")
        col_pdf1, col_pdf2 = st.columns(2)
        
        with col_pdf1:
            if st.button("Generate Class Notes PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt="NeuralBridge Class Notes", ln=True, align='C')
                pdf.set_font("Arial", size=12)
                pdf.ln(10)
                pdf.multi_cell(0, 10, txt=st.session_state.class_content)
                pdf_file = "class_notes.pdf"
                pdf.output(pdf_file)
                with open(pdf_file, "rb") as f:
                    st.download_button("Download Notes", f, file_name="Class_Notes.pdf")

        with col_pdf2:
            if st.button("Generate Attendance PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt="Attendance Report", ln=True, align='C')
                pdf.set_font("Arial", size=12)
                pdf.ln(10)
                for s in students:
                    pdf.cell(200, 10, txt=f"- {s['name']} (Roll: {s['roll']})", ln=True)
                pdf_file = "attendance.pdf"
                pdf.output(pdf_file)
                with open(pdf_file, "rb") as f:
                    st.download_button("Download Attendance", f, file_name="Attendance.pdf")
