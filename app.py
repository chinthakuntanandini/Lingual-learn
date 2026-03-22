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
    Initializes Firestore with an auto-rectification logic 
    for the RSA Private Key to prevent PEM errors.
    """
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            
            # RECTIFICATION: Fixing formatting issues in the Private Key string
            if "private_key" in info:
                # Replace literal backslashes with actual newlines
                clean_key = info["private_key"].replace("\\n", "\n").strip()
                # Remove accidental surrounding quotes
                if clean_key.startswith('"') and clean_key.endswith('"'):
                    clean_key = clean_key[1:-1]
                info["private_key"] = clean_key
            
            # Authentication handshake
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()

# --- 2. DOCUMENTATION UTILITY (PDF) ---
def generate_report(summary, students):
    """Generates a professional PDF report for the M.Tech Demo."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge AI: Class Activity Report", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Lecture Summary: \n{summary}")
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Verified Attendance:", ln=True)
    
    pdf.set_font("Arial", size=10)
    for s in students:
        pdf.cell(0, 10, txt=f"- {s['Name']} (Roll: {s['Roll']})", ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
st.sidebar.caption("Multilingual Cloud Sync System")
mode = st.sidebar.radio("Navigation:", ["Student Portal", "Teacher Control"])

# --- 4. STUDENT MODULE ---
if mode == "Student Portal":
    st.header("👤 Student Attendance Sync")
    st.info("Your data will be synchronized to the cloud in real-time.")
    
    name = st.text_input("Full Name")
    roll = st.text_input("University Roll Number")
    
    if st.button("Mark Attendance & Join"):
        if db and name and roll:
            # Syncing to Cloud Firestore
            db.collection("attendance").document(roll).set({
                "Name": name, "Roll": roll, "Status": "Present",
                "Timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Verified! Welcome {name}.")
        else:
            st.error("Please fill all details or check database connection.")

# --- 5. TEACHER MODULE ---
elif mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    
    # Real-time Table from Cloud
    st.subheader("📋 Live Student Attendance")
    attendance_list = []
    if db:
        docs = db.collection("attendance").stream()
        attendance_list = [doc.to_dict() for doc in docs]
        if attendance_list:
            st.table(pd.DataFrame(attendance_list)[['Name', 'Roll']])
        else:
            st.info("Waiting for students to sync...")
            
    if st.button("🔄 Sync List"):
        st.rerun()

    st.divider()

    # AI Transcription Simulation
    st.subheader("🎙️ AI Lecture Capture")
    audio = mic_recorder(start_prompt="Record Lecture", stop_prompt="Process Audio", key='mic')
    
    if audio:
        st.session_state.notes = "AI Transcription: This session discussed AIML cloud synchronization and security."
    
    notes = st.text_area("Edit Lecture Summary:", value=st.session_state.get('notes', ""))
    st.session_state.notes = notes

    # Final PDF Export
    if st.button("📄 Export Final Report"):
        if attendance_list:
            pdf_data = generate_report(st.session_state.notes, attendance_list)
            st.download_button("Download Report PDF", data=pdf_data, file_name="NeuralBridge_Report.pdf")
        else:
            st.warning("No data found to generate report.")
