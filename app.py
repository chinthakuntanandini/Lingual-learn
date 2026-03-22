import streamlit as st
from googletrans import Translator
from gtts import gTTS
import tempfile
from fpdf import FPDF

translator = Translator()

# ---------------- STORAGE ----------------
if "requests" not in st.session_state:
    st.session_state.requests = []

if "approved" not in st.session_state:
    st.session_state.approved = []

if "class_content" not in st.session_state:
    st.session_state.class_content = ""

# ---------------- UI ----------------
st.set_page_config(page_title="NeuralBridge AI", layout="wide")

page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: AI Smart Classroom")

# ---------------- STUDENT ----------------
if page == "Student Join":
    st.header("Student Registration")

    name = st.text_input("Enter Name")
    roll = st.text_input("Enter Roll No")
    lang = st.selectbox("Select Language", ["te", "hi", "en", "ta"])

    if st.button("Join"):
        if name and roll:
            st.session_state.requests.append({
                "name": name,
                "roll": roll,
                "language": lang
            })
            st.success("Request Sent!")
            st.rerun()
        else:
            st.warning("Enter details")

# ---------------- TEACHER ----------------
elif page == "Teacher Dashboard":
    st.header("Teacher Panel")

    if len(st.session_state.requests) == 0:
        st.info("No requests")
    else:
        for i, req in enumerate(st.session_state.requests):
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"{req['name']} ({req['roll']}) - {req['language']}")
            with col2:
                if st.button("Approve", key=i):
                    st.session_state.approved.append(req)
                    st.session_state.requests.remove(req)
                    st.rerun()

# ---------------- LIVE CLASS ----------------
elif page == "Live Class":
    st.header("📚 Live Class")

    # Teacher input
    content = st.text_input("Enter Class Content")

    if st.button("Send Class"):
        st.session_state.class_content = content
        st.success("Class Updated!")
        st.rerun()

    st.subheader("Students")

    if len(st.session_state.approved) == 0:
        st.warning("No students approved yet")
    else:
        for stu in st.session_state.approved:
            st.write(f"{stu['name']} ({stu['language']})")

    st.markdown("---")

    st.subheader("🌐 Translated Content + Audio")

    if st.session_state.class_content != "":
        for stu in st.session_state.approved:
            translated = translator.translate(
                st.session_state.class_content,
                dest=stu["language"]
            )

            st.write(f"👨‍🎓 {stu['name']} → {translated.text}")

            # 🔊 Audio
            tts = gTTS(translated.text, lang=stu["language"])
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            tts.save(temp_file.name)

            st.audio(temp_file.name)

    # ---------------- PDF SECTION ----------------

    st.markdown("---")
    st.subheader("📄 Download Reports")

    # Class PDF
    if st.button("Download Class PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Class Notes", ln=True)
        pdf.multi_cell(0, 10, st.session_state.class_content)

        pdf.output("class_notes.pdf")

        with open("class_notes.pdf", "rb") as f:
            st.download_button("Download Class PDF", f, file_name="class_notes.pdf")

    # Attendance PDF
    if st.button("Download Attendance PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Attendance List", ln=True)

        for stu in st.session_state.approved:
            pdf.cell(200, 10, txt=f"{stu['name']} - {stu['roll']}", ln=True)

        pdf.output("attendance.pdf")

        with open("attendance.pdf", "rb") as f:
            st.download_button("Download Attendance", f, file_name="attendance.pdf")
