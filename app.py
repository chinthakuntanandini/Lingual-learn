import streamlit as st
import pandas as pd
from fpdf import FPDF
from deep_translator import GoogleTranslator
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIG & SESSION STATE ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")

if 'approved_list' not in st.session_state:
    # Demo కోసం కొంతమంది స్టూడెంట్స్ డేటా
    st.session_state.approved_list = [
        {"Name": "Nandini", "Roll": "193H1A0508", "Status": "Present"},
        {"Name": "Kumar", "Roll": "193H1A0509", "Status": "Present"}
    ]
if 'live_content' not in st.session_state: st.session_state.live_content = ""
if 'class_table' not in st.session_state: st.session_state.class_table = pd.DataFrame()

# --- 2. PDF GENERATOR ---
def create_final_report(summary, table_df, attendance_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge: Final Class Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Lecture Summary: \n{summary}")
    
    # Attendance Section in PDF
    pdf.ln(10)
    pdf.cell(0, 10, txt="Attendance List:", ln=True)
    for student in attendance_list:
        pdf.cell(0, 10, txt=f"- {student['Name']} ({student['Roll']}): {student['Status']}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 3. SIDEBAR ---
st.sidebar.title("🎓 NeuralBridge AI")
user_role = st.sidebar.radio("Select Your Role:", ["Student", "Teacher"])

# --- 4. TEACHER MODULE ---
if user_role == "Teacher":
    t_page = st.sidebar.selectbox("Teacher Menu", ["Class Control & AI Table", "Approval Dashboard"])

    if t_page == "Class Control & AI Table":
        st.header("🎙️ Teacher Control Room")
        
        # Section 1: Attendance (ఇది ఇప్పుడు కొత్తగా యాడ్ చేశాను)
        st.subheader("📋 Live Attendance Tracker")
        if st.session_state.approved_list:
            att_df = pd.DataFrame(st.session_state.approved_list)
            st.table(att_df)
        else:
            st.info("No students approved yet.")

        st.divider()

        # Section 2: Speak to Lecture
        st.subheader("🎙️ 1. Speak to Lecture")
        audio = mic_recorder(start_prompt="▶️ Start Speaking", stop_prompt="🛑 Stop & Process", key='t_mic')
        if audio:
            st.session_state.live_content = "AI captured: Today's topic is about Neural Networks and Database Connectivity."
        
        teacher_edit = st.text_area("Edit Live Content:", value=st.session_state.live_content)
        st.session_state.live_content = teacher_edit

        st.divider()

        # Section 3: Speak to Table
        st.subheader("📊 2. AI Table (Speak to Create)")
        if st.button("Generate Summary Table"):
            data = {"Topic": ["Introduction", "Architecture", "Demo"], "Time": ["10 min", "20 min", "15 min"]}
            st.session_state.class_table = pd.DataFrame(data)
            st.table(st.session_state.class_table)

        st.divider()

        # Section 4: Reports
        st.subheader("📥 3. Final Reports")
        if st.button("Prepare Final PDF"):
            pdf_bytes = create_final_report(
                st.session_state.live_content, 
                st.session_state.class_table, 
                st.session_state.approved_list
            )
            st.download_button("Download Complete Class Report", data=pdf_bytes, file_name="Final_Report.pdf")

# (Student & Approval Dashboard logic follows...)
