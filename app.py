import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. SECURE DATABASE INITIALIZATION ---
@st.cache_resource
def init_db():
    """
    Initializes the connection to Google Cloud Firestore.
    Includes a 'Key Normalization' script to fix PEM formatting errors 
    and prevent InvalidByte/RSA loading failures.
    """
    try:
        if "firebase" in st.secrets:
            # Load secrets into a dictionary for processing
            info = dict(st.secrets["firebase"])
            
            # RECTIFICATION: Cleaning the Private Key string
            if "private_key" in info:
                # 1. Strip any accidental outer quotes or whitespace
                clean_key = info["private_key"].strip().strip('"').strip("'")
                
                # 2. Replace literal string '\n' with actual newline characters
                clean_key = clean_key.replace("\\n", "\n")
                
                # 3. Ensure the key has a proper ending to satisfy PKCS#8 standards
                if not clean_key.endswith("\n"):
                    clean_key += "\n"
                
                info["private_key"] = clean_key
            
            # Generate credentials and establish Firestore client
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        # Display the specific authentication error if the connection fails
        st.error(f"❌ Connection Error: {e}")
    return None

# Global Database Object
db = init_db()

# --- 2. REPORT GENERATION LOGIC ---
def generate_pdf_report(summary, student_data):
    """
    Generates a professional PDF report containing the lecture summary 
    and the list of verified students.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge AI: Class Activity Report", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Lecture Summary:\n{summary}")
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Verified Attendance List:", ln=True)
    
    # Iterate through students and add to PDF
    pdf.set_font("Arial", size=10)
    for student in student_data:
        pdf.cell(0, 10, txt=f"- {student.get('Name')} (Roll: {student.get('Roll')})", ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- 3. USER INTERFACE (UI) NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
st.sidebar.caption("Real-time Multilingual Sync System")
app_mode = st.sidebar.radio("Navigation:", ["Student Portal", "Teacher Control"])

# --- 4. STUDENT MODULE ---
if app_mode == "Student Portal":
    st.header("👤 Student Attendance Sync")
    st.info("Your details will be synchronized to the cloud in real-time.")
    
    s_name = st.text_input("Full Name")
    s_roll = st.text_input("University Roll Number")
    
    if st.button("Mark Attendance & Join"):
        if db and s_name and s_roll:
            # Synchronizing student data to the Cloud Firestore 'attendance' collection
            db.collection("attendance").document(s_roll).set({
                "Name": s_name,
                "Roll": s_roll,
                "Status": "Present",
                "Timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Verified! Welcome {s_name}. Your session is active.")
        else:
            st.error("Please fill all details and ensure the database is connected.")

# --- 5. TEACHER MODULE ---
elif app_mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    
    # Displaying Real-time Student List
    st.subheader("📋 Live Student Attendance")
    attendance_list = []
    if db:
        # Fetch all documents from the 'attendance' collection
        docs = db.collection("attendance").stream()
        attendance_list = [doc.to_dict() for doc in docs]
        
        if attendance_list:
            # Render the list as a DataFrame table
            st.table(pd.DataFrame(attendance_list)[['Name', 'Roll']])
        else:
            st.info("Waiting for students to join the session...")
            
    if st.button("🔄 Sync Attendance"):
        st.rerun()

    st.divider()

    # AI Audio Transcription Module
    st.subheader("🎙️ AI Lecture Capture")
    audio = mic_recorder(start_prompt="Record Lecture", stop_prompt="Stop & Process", key='teacher_mic')
    
    if audio:
        # Mock transcription for the project demonstration
        st.session_state.lecture_notes = "AI Analysis: The session discussed Cloud-based AIML architecture and RSA encryption standards."
    
    notes = st.text_area("Final Summary (Editable):", value=st.session_state.get('lecture_notes', ""))
    st.session_state.lecture_notes = notes

    # Final PDF Export
    if st.button("📄 Export Final Report"):
        if attendance_list:
            pdf_data = generate_pdf_report(st.session_state.lecture_notes, attendance_list)
            st.download_button("Download Report PDF", data=pdf_data, file_name="NeuralBridge_Report.pdf")
        else:
            st.warning("Attendance data is required to generate a report.")
