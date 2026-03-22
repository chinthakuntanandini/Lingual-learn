import streamlit as st
from googletrans import Translator
from gtts import gTTS
import tempfile
from fpdf import FPDF
import pandas as pd
import speech_recognition as sr
from google.cloud import firestore
from google.oauth2 import service_account

translator = Translator()

# ---------------- FIREBASE CONNECTION ----------------
@st.cache_resource
def init_connection():
    firebase_info = st.secrets["firebase"]
    private_key = firebase_info["private_key"].replace("\\n", "\n")

    creds_dict = dict(firebase_info)
    creds_dict["private_key"] = private_key

    creds = service_account.Credentials.from_service_account_info(creds_dict)
    return firestore.Client(credentials=creds)

db = init_connection()

# ---------------- UI ----------------
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])
st.title("🎓 NeuralBridge: AI Smart Classroom")

lang_map = {"te": "Telugu", "ur": "Urdu", "en": "English"}

# ---------------- STUDENT ----------------
if page == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Name")
    roll = st.text_input("Enter Roll Number")
    lang = st.selectbox("Select Language", {"Telugu": "te", "Urdu": "ur", "English": "en"})

    if st.button("Join"):
        if name and roll:
            db.collection("requests").document(roll).set({
                "name": name,
                "roll": roll,
                "language": lang,
                "status": "pending"
            })
            st.success("Request Sent to Teacher!")
        else:
            st.warning("Enter all details")

# ---------------- TEACHER ----------------
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    requests = db.collection("requests").where("status", "==", "pending").stream()
    found = False
    for doc in requests:
        found = True
        data = doc.to_dict()
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"{data['name']} ({data['roll']}) - {lang_map[data['language']]}")
        with col2:
            if st.button("Approve", key=doc.id):
                db.collection("requests").document(doc.id).update({"status": "approved"})
                st.rerun()
    if not found:
        st.info("No pending requests")

# ---------------- LIVE CLASS ----------------
elif page == "Live Class":
    st.header("🎤 Teacher Voice Enabled Class (Upload .wav)")

    uploaded_file = st.file_uploader("Upload Teacher Voice (.wav)", type=["wav"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio:
            temp_audio.write(uploaded_file.read())
            temp_path = temp_audio.name

        r = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            audio = r.record(source)
            try:
                text = r.recognize_google(audio)
                st.session_state.class_content = text
                st.success("Voice converted to text!")
                st.write("📚 Text:", text)
            except:
                st.error("Could not recognize audio")

    st.markdown("---")

    st.subheader("👨‍🎓 Students")
    approved = db.collection("requests").where("status", "==", "approved").stream()
    students = []
    for doc in approved:
        data = doc.to_dict()
        students.append(data)
        st.write(f"{data['name']} ({lang_map[data['language']]})")
    if len(students) == 0:
        st.warning("No students approved yet")

    st.markdown("---")

    if "class_content" in st.session_state:
        st.subheader("🌐 Translated Content + Audio")
        for stu in students:
            translated = translator.translate(st.session_state.class_content, dest=stu["language"])
            st.write(f"{stu['name']} → {translated.text}")
            tts = gTTS(translated.text, lang=stu["language"])
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            tts.save(temp_file.name)
            st.audio(temp_file.name)

        st.subheader("📊 Class Table")
        table_data = {
            "Topic": [st.session_state.class_content],
            "Students Count": [len(students)],
            "Languages Used": [", ".join(set([s["language"] for s in students]))]
        }
        df = pd.DataFrame(table_data)
        st.table(df)

        st.subheader("📈 Diagram")
        chart_data = {
            "Languages": ["Telugu", "Urdu", "English"],
            "Students": [
                sum(1 for s in students if s["language"] == "te"),
                sum(1 for s in students if s["language"] == "ur"),
                sum(1 for s in students if s["language"] == "en")
            ]
        }
        chart_df = pd.DataFrame(chart_data)
        st.bar_chart(chart_df.set_index("Languages"))

        st.subheader("📄 Download Reports")
        if st.button("Download Class PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Class Notes", ln=True)
            pdf.multi_cell(0, 10, st.session_state.class_content)
            pdf.output("class_notes.pdf")
            with open("class_notes.pdf", "rb") as f:
                st.download_button("Download Class PDF", f)

        if st.button("Download Attendance PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Attendance", ln=True)
            for stu in students:
                pdf.cell(200, 10, txt=f"{stu['name']} - {stu['roll']}", ln=True)
            pdf.output("attendance.pdf")
            with open("attendance.pdf", "rb") as f:
                st.download_button("Download Attendance PDF", f)
