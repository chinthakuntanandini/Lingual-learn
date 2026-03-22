import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. FIREBASE CONNECTION LOGIC ---
@st.cache_resource
def init_db():
    """
    Establishes a secure connection to Google Firestore.
    Uses @st.cache_resource to maintain a single connection throughout the session.
    """
    try:
        if "firebase" in st.secrets:
            # Load service account credentials from Streamlit Secrets
            info = dict(st.secrets["firebase"])
            
            # CRITICAL FIX: Normalizing the RSA Private Key formatting
            if "private_key" in info:
                # Replace literal backslashes with actual newlines for valid PEM format
                key = info["private_key"].replace("\\n", "\n").strip()
                
                # Remove accidental surrounding quotes from the secret string
                if key.startswith('"') and key.endswith('"'):
                    key = key[1:-1]
                
                info["private_key"] = key
            
            # Create credentials object from the service account info
            creds = service_account.Credentials.from_service_account_info(info)
            
            # Initialize and return the Firestore Client
            return firestore.Client(credentials=creds, project=creds.project_id)
            
    except Exception as e:
        # Display connection errors (like the PEM 'InvalidByte' error) for debugging
        st.error(f"❌ Firebase Connection Error: {e}")
    
    return None

# Global Database Instance
db = init_db()

# --- 2. PDF GENERATION UTILITY ---
def create_final_report(summary, attendance_list):
    """
    Generates a professional PDF report containing the lecture summary and student attendance.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge: AI Classroom Final Report", ln=True, align='C')
    
    # Section: Lecture Summary
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Lecture Highlights: \n{summary}")
    
    # Section: Attendance Table
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Student Attendance List:", ln=True)
    pdf.set_font("Arial", size=10)
    
    if attendance_list:
        for student in attendance_list:
            pdf.cell(0, 10, txt=f"- {student['Name']} (Roll: {student['Roll']}): PRESENT", ln=True)
    else:
        pdf.cell(0, 10, txt="No students recorded.", ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
user_role = st.sidebar.radio("Select Your Role:", ["Student", "Teacher"])

# --- 4. STUDENT MODULE ---
if user_role == "Student":
    st.header("👤 Student Registration Portal")
    st.info("Enter your details to join the live class.")
    
    s_name = st.text_input("Full Name")
    s_roll = st.text_input("University Roll Number")
    
    if st.button("✅ Join Class & Mark Attendance"):
        if db and s_name and s_roll:
            # Writing student data to the 'attendance' collection in Firestore
            db.collection("attendance").document(s_roll).set({
                "Name": s_name,
                "Roll": s_roll,
                "Status": "Present",
                "Timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Welcome {s_name}! Your attendance has been synchronized with the Teacher.")
        else:
            st.warning("Please provide both Name and Roll Number.")

# --- 5. TEACHER MODULE ---
elif user_role == "Teacher":
    st.header("🎙️ Teacher Command Center")
    
    # Subsection: Live Attendance Tracking
    st.subheader("📋 Real-time Attendance Tracker")
    attendance_data = []
    
    if db:
        # Fetching live data from Firestore
        docs = db.collection("attendance").stream()
        attendance_data = [doc.to_dict() for doc in docs]
        
        if attendance_data:
            df = pd.DataFrame(attendance_data)[['Name', 'Roll', 'Status']]
            st.table(df) # Displays the list of joined students
        else:
            st.info("Waiting for students to connect...")
    
    if st.button("🔄 Refresh Student List"):
        st.rerun()

    st.divider()

    # Subsection: AI-Powered Lecture capture
    st.subheader("🎙️ 1. Live AI Transcription")
    audio = mic_recorder(start_prompt="▶️ Start Lecture", stop_prompt="🛑 Stop & Process", key='teacher_audio')
    
    if audio:
        # Simulation of Speech-to-Text conversion
        st.session_state.lecture_notes = "AI Transcription: Today's AIML session covers Cloud Data synchronization and RSA encryption keys."
    
    # Editable text area for the teacher to refine notes
    final_notes = st.text_area("Lecture Content Summary:", value=st.session_state.get('lecture_notes', ""))
    st.session_state.lecture_notes = final_notes

    st.divider()

    # Subsection: Automated Report Generation
    st.subheader("📥 2. Export & Reporting")
    if st.button("📄 Generate Final Class PDF"):
        if attendance_data:
            pdf_data = create_final_report(st.session_state.get('lecture_notes', "No notes recorded."), attendance_data)
            st.download_button(
                label="Download Official Class Report",
                data=pdf_data,
                file_name="NeuralBridge_Class_Report.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Report cannot be generated without attendance data.")
