import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            # కీ లో ఉన్న స్పెషల్ క్యారెక్టర్స్ ని సరిచేయడం
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
    return None

db = init_db()

# --- 2. PDF GENERATOR FUNCTION ---
def create_final_report(summary, attendance_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge: Class Final Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Class Summary/Lecture: \n{summary}")
    
    pdf.ln(10)
    pdf.cell(0, 10, txt="Attendance List:", ln=True)
    for index, row in attendance_df.iterrows():
        pdf.cell(0, 10, txt=f"- {row['Name']} ({row['Roll']}): {row['Status']}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
user_role = st.sidebar.radio("Select Your Role:", ["Student", "Teacher"])

# --- 4. STUDENT MODULE ---
if user_role == "Student":
    st.header("👤 Student Portal")
    s_name = st.text_input("Full Name")
    s_roll = st.text_input("Roll No")
    
    if st.button("Join Class"):
        if db and s_name and s_roll:
            db.collection("attendance").document(s_roll).set({
                "Name": s_name, "Roll": s_roll, "Status": "Present"
            })
            st.success(f"Done! {s_name}, you are marked Present.")
        else:
            st.error("Please fill details correctly.")

# --- 5. TEACHER MODULE ---
elif user_role == "Teacher":
    st.header("🎙️ Teacher Control Room")
    
    # Live Attendance Tracker
    st.subheader("📋 Live Attendance Tracker")
    attendance_list = []
    if db:
        docs = db.collection("attendance").stream()
        attendance_list = [doc.to_dict() for doc in docs]
        if attendance_list:
            att_df = pd.DataFrame(attendance_list)
            st.table(att_df)
        else:
            st.info("No students joined yet.")
    
    if st.button("🔄 Refresh List"):
        st.rerun()

    st.divider()

    # Live Lecture Section
    st.subheader("🎙️ 1. Live Lecture (Speak)")
    audio = mic_recorder(start_prompt="▶️ Start Speaking", stop_prompt="🛑 Stop", key='t_mic')
    if audio:
        # ఇక్కడ AI మాటలను టెక్స్ట్ గా మారుస్తుంది (Simulated)
        st.session_state.lecture_notes = "AI Captured: Today we discussed Cloud integration in AIML."
    
    lecture_text = st.text_area("Lecture Content:", value=st.session_state.get('lecture_notes', ""))
    st.session_state.lecture_notes = lecture_text

    st.divider()

    # Final Reports Section
    st.subheader("📥 2. Final Reports")
    if st.button("Prepare Final PDF"):
        if attendance_list:
            pdf_bytes = create_final_report(st.session_state.get('lecture_notes', ""), pd.DataFrame(attendance_list))
            st.download_button("Download Class PDF", data=pdf_bytes, file_name="Class_Report.pdf")
            st.success("PDF is ready for download!")
        else:
            st.warning("Cannot generate PDF without attendance.")
