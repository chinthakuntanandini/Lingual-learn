import streamlit as st
import pandas as pd
from fpdf import FPDF
from deep_translator import GoogleTranslator
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide", page_icon="🎓")

# --- 2. PDF GENERATOR FUNCTION ---
def create_final_report(summary, table_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NeuralBridge: Class Summary & Analytics", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Lecture Summary: \n{summary}")
    
    if not table_df.empty:
        pdf.ln(10)
        pdf.cell(0, 10, txt="Class Data Table:", ln=True)
        pdf.set_font("Arial", size=10)
        # Simple Table rendering in PDF
        for index, row in table_df.iterrows():
            line = " | ".join([str(v) for v in row.values])
            pdf.cell(0, 10, txt=line, ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- 3. ROLE SELECTION (Sidebar) ---
st.sidebar.title("🎓 NeuralBridge AI")
user_role = st.sidebar.radio("Select Your Role:", ["Student", "Teacher"])

# Initialize session states if not present
if 'approved' not in st.session_state: st.session_state.approved = False
if 'live_content' not in st.session_state: st.session_state.live_content = ""
if 'class_table' not in st.session_state: st.session_state.class_table = pd.DataFrame()

# --- 4. STUDENT MODULE ---
if user_role == "Student":
    st.header("👤 Student Portal")
    with st.expander("Register for Class", expanded=not st.session_state.approved):
        name = st.text_input("Name")
        roll = st.text_input("Roll No")
        lang = st.selectbox("Preferred Language", ["Telugu", "Hindi", "English"])
        if st.button("Join Class"):
            st.info("Request sent! Waiting for Teacher's approval...")

    st.divider()
    st.subheader("📢 Live Class Updates")
    if st.session_state.approved:
        st.success(f"Connected! Viewing updates in {lang}")
        # Translate live content for the student
        translated = GoogleTranslator(source='auto', target=lang.lower()[:2]).translate(st.session_state.live_content)
        st.write(f"**Lecture Feed:** {translated}")
        if not st.session_state.class_table.empty:
            st.write("**Class Data Table:**")
            st.table(st.session_state.class_table)
    else:
        st.warning("You will see the lecture once the Teacher approves you.")

# --- 5. TEACHER MODULE ---
else:
    st.sidebar.divider()
    t_page = st.sidebar.selectbox("Teacher Menu", ["Class Control & AI Table", "Approval Dashboard"])

    if t_page == "Class Control & AI Table":
        st.header("🎙️ Teacher Control Room")
        
        # Speak to Text
        st.subheader("1. Speak to Lecture")
        audio = mic_recorder(start_prompt="▶️ Start Speaking", stop_prompt="🛑 Stop & Process", key='teacher_mic')
        if audio:
            st.session_state.live_content = "AI Transcribed: Today we are learning about Artificial Intelligence and Cloud Data."
            st.success("Speech captured and broadcasted!")

        teacher_edit = st.text_area("Live Content (Edit if needed):", value=st.session_state.live_content)
        st.session_state.live_content = teacher_edit

        st.divider()
        st.subheader("2. Speak to Table (AI Automation)")
        st.write("Command Example: 'Create a summary table'")
        if st.button("Generate AI Table"):
            # Simulation of speech-to-table logic
            data = {"Topic": ["AI Basics", "Firebase", "Translation"], "Status": ["Done", "Live", "Ready"]}
            st.session_state.class_table = pd.DataFrame(data)
            st.table(st.session_state.class_table)
            st.success("Table generated from command!")

        st.divider()
        st.subheader("3. Final Reports")
        if st.button("📥 Prepare Final Class PDF"):
            pdf_bytes = create_final_report(st.session_state.live_content, st.session_state.class_table)
            st.download_button("Download & Share PDF", data=pdf_bytes, file_name="Class_Report.pdf")

    elif t_page == "Approval Dashboard":
        st.header("👨‍🏫 Student Approvals")
        st.write("Pending Requests:")
        st.info("Student: Nandu (193H1A0508) is waiting.")
        if st.button("Approve All Students"):
            st.session_state.approved = True
            st.success("Students approved! They can now see the live feed.")
