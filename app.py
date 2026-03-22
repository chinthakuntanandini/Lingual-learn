import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. SECURE CLOUD DATABASE CONNECTION ---
@st.cache_resource
def init_db():
    """
    Establishes a connection to Google Cloud Firestore.
    Includes logic to normalize the RSA Private Key to prevent PEM errors.
    """
    try:
        if "firebase" in st.secrets:
            # Convert secrets to a mutable dictionary
            info = dict(st.secrets["firebase"])
            
            # KEY RECTIFICATION: Fixing formatting issues in the RSA Private Key string
            if "private_key" in info:
                # Replace literal backslashes with actual newlines for PKCS#8 compliance
                clean_key = info["private_key"].replace("\\n", "\n").strip()
                
                # Remove accidental surrounding quotes from the string
                if clean_key.startswith('"') and clean_key.endswith('"'):
                    clean_key = clean_key[1:-1]
                
                info["private_key"] = clean_key
            
            # Authenticate using the service account info
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        # Displaying the specific authentication error for debugging
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()

# --- 2. REPORT GENERATION UTILITY ---
def generate_report(summary, students):
    """Generates a professional PDF document of the class activity."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge AI: Class Activity Report", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Lecture Summary: \n{summary}")
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Verified Student Attendance:", ln=True)
    
    # List each student's name and roll number in the PDF
    for s in students:
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, txt=f"- {s.get('Name')} (Roll: {s.get('Roll')})", ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
st.sidebar.caption("Real-time Multilingual Sync System")
mode = st.sidebar.radio("Navigation:", ["Student Portal", "Teacher Control"])

# --- 4. STUDENT PORTAL MODULE ---
if mode == "Student Portal":
    st.header("👤 Student Attendance Sync")
    st.info("Your details will be synchronized to the cloud in real-time.")
    
    name = st.text_input("Full Name")
    roll = st.text_input("University Roll Number")
    
    if st.button("Mark Attendance & Join"):
        if db and name and roll:
            # Pushing student data to Google Cloud Firestore
            db.collection("attendance").document(roll).set({
                "Name": name, "Roll": roll, "Status": "Present",
                "Timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Verified! Welcome {name}. Data synced to cloud.")
        else:
            st.error("Please fill all details and ensure the database is connected.")

# --- 5. TEACHER CONTROL MODULE ---
elif mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    
    # Live Data Sync from Firestore
    st.subheader("📋 Live Student Attendance")
    attendance_list = []
    if db:
        # Fetching documents from the 'attendance' collection
        docs = db.collection("attendance").stream()
        attendance_list = [doc.to_dict() for doc in docs]
        
        if attendance_list:
            # Displaying attendance in a structured table
            st.table(pd.DataFrame(attendance_list)[['Name', 'Roll']])
        else:
            st.info("Waiting for students to connect...")
            
    if st.button("🔄 Sync List"):
        st.rerun()

    st.divider()

    # AI Lecture Transcription Simulation
    st.subheader("🎙️ AI Lecture Capture")
    audio = mic_recorder(start_prompt="Record Lecture", stop_prompt="Process Audio", key='mic')
    
    if audio:
        # Mocking the AI output for the project demonstration
        st.session_state.notes = "AI Analysis: The session discussed Cloud-based AIML architecture and RSA encryption."
    
    notes = st.text_area("Final Summary (Editable):", value=st.session_state.get('notes', ""))
    st.session_state.notes = notes

    # Final PDF Exporting Section
    if st.button("📄 Export Final Report"):
        if attendance_list:
            pdf_data = generate_report(st.session_state.notes, attendance_list)
            st.download_button("Download Report PDF", data=pdf_data, file_name="NeuralBridge_Report.pdf")
        else:
            st.warning("No attendance data found to generate a report.")
