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
# Using cache_resource to prevent multiple connection attempts
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            st.error("Firebase secrets not found!")
            return None
            
        firebase_info = st.secrets["firebase"]
        # Essential Fix: Replace literal \n with actual newline for the PEM key
        raw_key = firebase_info["private_key"]
        private_key = raw_key.replace("\\n", "\n").strip().strip('"')

        creds_dict = dict(firebase_info)
        creds_dict["private_key"] = private_key

        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        return None

db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: AI Smart Classroom")

# Language Mappings for UI and Codes
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
            try:
                # Saving student request to Firestore
                db.collection("requests").document(roll).set({
                    "name": name,
                    "roll": roll,
                    "language": lang_code,
                    "status": "pending"
                })
                st.success(f"Request sent! {name}, please wait for Teacher's approval.")
            except Exception as e:
                st.error(f"Firestore Error: {e}")
        else:
            st.warning("Please provide all details.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    if db:
        try:
            # Fetching pending requests
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
        except Exception as e:
            st.error(f"Error fetching requests: {e}")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("🎤 Live Session (Voice Enabled)")
    
    # Audio Upload Section
    uploaded_file = st.file_uploader("Upload Teacher's Voice (.wav)", type=["wav"])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(uploaded_file.read())
            temp_path = temp_audio.name

        r = sr.Recognizer()
        try:
            with sr.AudioFile(temp_path) as source:
                audio_data = r.record(source)
                # Converting Speech to English Text
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
    
    # Approved Students Display
    students = []
    if db:
        approved = db.collection("requests").where("status", "==", "approved").stream()
        for doc in approved:
            data = doc.to_dict()
            students.append(data)
    
    if "class_content" in st.session_state and students:
        st.subheader("🌐 Multilingual Translation & Audio")
        
        for stu in students:
            try:
                # Using Deep Translator for better stability
                translated_text = GoogleTranslator(source='auto', target=stu["language"]).translate(st.session_state.class_content)
                
                st.write(f"🔔 **For {stu['name']} ({lang_map[stu['language']]}):**")
                st.success(translated_text)
                
                # Text-to-Speech Generation
                tts = gTTS(translated_text, lang=stu["language"])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.name)
                    st.audio(fp.name)
            except Exception as e:
                st.error(f"Error for student {stu['name']}: {e}")

        # --- Statistics Table ---
        st.subheader("📊 Session Summary")
        summary_df = pd.DataFrame({
            "Metric": ["Total Students", "Languages Active"],
            "Value": [len(students), ", ".join(set([lang_map[s["language"]] for s in students]))]
        })
        st.table(summary_df)

        # --- Reports Generation ---
        st.subheader("📄 Class Documents")
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Create Lesson PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt="NeuralBridge: Class Notes", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=st.session_state.class_content)
                pdf.output("notes.pdf")
                with open("notes.pdf", "rb") as f:
                    st.download_button("Download Notes", f, file_name="Class_Notes.pdf")

        with col_b:
            if st.button("Create Attendance"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt="Attendance Report", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                for s in students:
                    pdf.cell(200, 10, txt=f"- {s['name']} (Roll: {s['roll']})", ln=True)
                pdf.output("attendance.pdf")
                with open("attendance.pdf", "rb") as f:
                    st.download_button("Download Attendance", f, file_name="Attendance.pdf")
    elif not students:
        st.warning("No students are approved in this session.")
