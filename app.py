import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from googletrans import Translator
import datetime

# --- 1. FIREBASE SETUP ---
if not firebase_admin._apps:
    cred = credentials.Certificate("key.json") # మీ key.json ఫైల్ పేరు ఇక్కడ ఉండాలి
    firebase_admin.initialize_app(cred)

db = firestore.client()
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
            doc_ref = db.collection("requests").document(roll_no)
            doc_ref.set({
                "name": name,
                "roll_no": roll_no,
                "language": lang,
                "status": "pending",
                "timestamp": datetime.datetime.now()
            })
            st.success(f"Request sent to teacher, {name}! Please wait for approval.")
        else:
            st.error("Please fill all details.")

# --- 5. TEACHER DASHBOARD ---
elif sidebar == "Teacher Dashboard":
    st.header("Teacher Control Panel")
    
    # Show Requests
    requests = db.collection("requests").where("status", "==", "pending").stream()
    
    st.subheader("Pending Requests")
    for req in requests:
        data = req.to_dict()
        col1, col2 = st.columns([3, 1])
        col1.write(f"ID: {data['roll_no']} | Name: {data['name']} | Lang: {data['language']}")
        if col2.button("Accept", key=data['roll_no']):
            db.collection("requests").document(data['roll_no']).update({"status": "accepted"})
            st.rerun()

    # Attendance PDF
    if st.button("Generate Attendance PDF"):
        accepted_students = db.collection("requests").where("status", "==", "accepted").stream()
        att_list = "Class Attendance Report\n" + "-"*30 + "\n"
        for s in accepted_students:
            d = s.to_dict()
            att_list += f"{d['roll_no']} - {d['name']}\n"
        
        fname = create_pdf(att_list, "attendance.pdf")
        with open(fname, "rb") as f:
            st.download_button("Download Attendance", f, file_name="attendance.pdf")

# --- 6. LIVE CLASS & VOICE ---
elif sidebar == "Live Class":
    st.header("Live Interactive Class")
    
    # Teacher Input
    topic = st.text_input("Class Topic")
    teacher_speech = st.text_area("Teacher's Speech (English)")
    
    if st.button("Start Class & Translate"):
        # Simulate translation for students
        all_students = db.collection("requests").where("status", "==", "accepted").stream()
        
        st.subheader("Translated Class Content")
        class_content = f"Topic: {topic}\nDate: {datetime.date.today()}\n\n"
        
        for s in all_students:
            data = s.to_dict()
            target_lang = data['language'].lower()[:2] # Get 'te', 'hi' etc
            translated = translator.translate(teacher_speech, dest=target_lang).text
            
            st.write(f"📝 **For {data['name']} ({data['language']}):**")
            st.info(translated)
            class_content += f"[{data['language']}] {translated}\n\n"
        
        # Table / Diagram Simulation
        st.table({"Points": ["Topic Introduction", "Main Concept", "Conclusion"]})
        
        # Save Class Notes PDF
        fname = create_pdf(class_content, "class_notes.pdf")
        with open(fname, "rb") as f:
            st.download_button("Download Class Notes PDF", f, file_name="class_notes.pdf")
