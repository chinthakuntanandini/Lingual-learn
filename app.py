import streamlit as st
from fpdf import FPDF
from googletrans import Translator
import datetime

# --- 1. INITIALIZE SESSION STATE (Firebase కి బదులుగా) ---
if 'requests' not in st.session_state:
    st.session_state['requests'] = {}
if 'class_log' not in st.session_state:
    st.session_state['class_log'] = ""

translator = Translator()

# --- 2. PDF GENERATION FUNCTION ---
def create_pdf(content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)
    return filename

# --- 3. UI HEADER ---
st.title("🎓 NeuralBridge: AI Smart Class")
sidebar = st.sidebar.radio("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

# --- 4. STUDENT JOIN PAGE ---
if sidebar == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Name")
    roll_no = st.text_input("Enter Roll Number")
    lang = st.selectbox("Select Language", ["Telugu", "Hindi", "Tamil", "English"])
    
    if st.button("Request to Join"):
        if name and roll_no:
            # డేటాను Session State లో సేవ్ చేస్తున్నాం
            st.session_state['requests'][roll_no] = {
                "name": name,
                "roll_no": roll_no,
                "language": lang,
                "status": "pending"
            }
            st.success(f"Request sent! Please wait for teacher approval, {name}.")
        else:
            st.error("Please fill all details.")

# --- 5. TEACHER DASHBOARD ---
elif sidebar == "Teacher Dashboard":
    st.header("Teacher Control Panel")
    
    st.subheader("Pending Requests")
    has_requests = False
    for roll, data in st.session_state['requests'].items():
        if data['status'] == "pending":
            has_requests = True
            col1, col2 = st.columns([3, 1])
            col1.write(f"ID: {roll} | Name: {data['name']} | Lang: {data['language']}")
            if col2.button("Accept", key=roll):
                st.session_state['requests'][roll]['status'] = "accepted"
                st.rerun()
    
    if not has_requests:
        st.info("No pending requests.")

    # Attendance PDF
    if st.button("Generate Attendance PDF"):
        att_list = "Class Attendance Report\n" + "-"*30 + "\n"
        for roll, data in st.session_state['requests'].items():
            if data['status'] == "accepted":
                att_list += f"{roll} - {data['name']}\n"
        
        fname = create_pdf(att_list, "attendance.pdf")
        with open(fname, "rb") as f:
            st.download_button("Download Attendance", f, file_name="attendance.pdf")

# --- 6. LIVE CLASS & VOICE ---
elif sidebar == "Live Class":
    st.header("Live Interactive Class")
    
    topic = st.text_input("Class Topic")
    teacher_speech = st.text_area("Teacher's Speech (English)")
    
    if st.button("Start Class & Translate"):
        st.subheader("Translated Content for Students")
        current_notes = f"Topic: {topic}\nDate: {datetime.date.today()}\n\n"
        
        accepted_students = [d for d in st.session_state['requests'].values() if d['status'] == "accepted"]
        
        if not accepted_students:
            st.warning("No students accepted yet!")
        else:
            for student in accepted_students:
                target_lang = student['language'].lower()[:2]
                translated = translator.translate(teacher_speech, dest=target_lang).text
                
                st.write(f"📝 **For {student['name']} ({student['language']}):**")
                st.info(translated)
                current_notes += f"[{student['language']}] {translated}\n\n"
            
            # Table/Diagram Simulation
            st.table({"Points": ["Introduction", "Main Concept", "Conclusion"]})
            
            # Save to PDF
            fname = create_pdf(current_notes, "class_notes.pdf")
            with open(fname, "rb") as f:
                st.download_button("Download Class Notes PDF", f, file_name="class_notes.pdf")
