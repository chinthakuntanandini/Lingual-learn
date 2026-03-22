import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. SECURE FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    """
    Initializes Firestore connection with professional error handling 
    and RSA key normalization to prevent PEM loading errors.
    """
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            
            # NORMALIZATION: Converts literal string '\n' into actual newline characters
            if "private_key" in info:
                # This fixes the 'InvalidByte' and PEM formatting issues
                info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()

# --- 2. PDF REPORT GENERATOR ---
def create_pdf(summary, attendance_list):
    """Generates a professional PDF report for the teacher."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge AI: Class Report", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Lecture Summary:\n{summary}")
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Attendance List:", ln=True)
    
    for student in attendance_list:
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, txt=f"- {student['Name']} (Roll: {student['Roll']})", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI LAYOUT ---
st.sidebar.title("🎓 NeuralBridge AI")
role = st.sidebar.radio("Switch View:", ["Student Portal", "Teacher Control"])

# --- 4. STUDENT MODULE ---
if role == "Student Portal":
    st.header("👤 Student Registration")
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    
    if st.button("Mark Attendance"):
        if db and name and roll:
            # Syncing data to Google Cloud Firestore
            db.collection("attendance").document(roll).set({
                "Name": name, "Roll": roll, "Status": "Present"
            })
            st.success(f"Verified! Welcome to class, {name}.")
        else:
            st.error("Please enter valid details.")

# --- 5. TEACHER MODULE ---
elif role == "Teacher Control":
    st.header("🎙️ Lecture & Attendance Center")
    
    # Real-time Table from Cloud
    st.subheader("📋 Live Student List")
    attendance_data = []
    if db:
        docs = db.collection("attendance").stream()
        attendance_data = [doc.to_dict() for doc in docs]
        if attendance_data:
            st.table(pd.DataFrame(attendance_data)[['Name', 'Roll']])
        else:
            st.info("No students have joined yet.")

    st.divider()
    
    # Speech-to-Text Module
    st.subheader("🎙️ AI Lecture Transcription")
    audio = mic_recorder(start_prompt="Record Lecture", stop_prompt="Stop Recording", key='mic')
    
    if audio:
        # Mock transcription for the demo
        st.session_state.notes = "Today's AIML lecture focused on Neural Networks and Cloud Integration."
    
    lecture_notes = st.text_area("Final Summary:", value=st.session_state.get('notes', ""))
    st.session_state.notes = lecture_notes

    # Export Section
    if st.button("Generate Final Report"):
        if attendance_data:
            pdf_bytes = create_pdf(st.session_state.notes, attendance_data)
            st.download_button("Download Class PDF", data=pdf_bytes, file_name="Class_Report.pdf")
        else:
            st.warning("No data to export.")
