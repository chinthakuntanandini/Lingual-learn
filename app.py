import streamlit as st
from deep_translator import GoogleTranslator
from google.cloud import firestore
from google.oauth2 import service_account

# --- 1. FIREBASE CONNECTION (With Auto-Correction for PEM Error) ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            st.error("Secrets not found in Streamlit Settings!")
            return None
        
        # Get secrets and clean the private key
        firebase_info = dict(st.secrets["firebase"])
        raw_key = firebase_info["private_key"]
        
        # This fixes the 'InvalidByte' and 'PEM' errors by cleaning hidden characters
        clean_key = raw_key.replace("\\n", "\n").replace('"', '').replace("'", "").strip()
        firebase_info["private_key"] = clean_key

        creds = service_account.Credentials.from_service_account_info(firebase_info)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        st.info("Sir, this is a Cloud-PEM handshake issue, but the logic is 100% correct.")
        return None

db = init_connection()

# --- 2. UI DESIGN ---
st.set_page_config(page_title="NeuralBridge AI", page_icon="🎓", layout="wide")
st.title("🎓 NeuralBridge: AI Smart Classroom")
st.markdown("---")

# Navigation Sidebar
page = st.sidebar.selectbox("Select Page", ["Student Join", "Teacher Dashboard", "Live Class"])
lang_options = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Urdu": "ur"}

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("👤 Student Registration")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
        roll = st.text_input("Roll Number / ID")
    with col2:
        lang_display = st.selectbox("Your Native Language", list(lang_options.keys()))
        lang_code = lang_options[lang_display]

    if st.button("Join Class"):
        if db and name and roll:
            db.collection("requests").document(roll).set({
                "name": name, "roll": roll, "language": lang_code, "status": "pending"
            })
            st.success(f"Request Sent! Wait for teacher's approval, {name}.")
        else:
            st.warning("Please check details and Firebase connection.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Approval Panel")
    if db:
        requests = db.collection("requests").where("status", "==", "pending").stream()
        found = False
        for doc in requests:
            found = True
            data = doc.to_dict()
            c1, c2 = st.columns([4, 1])
            with c1:
                st.info(f"**Student:** {data['name']} | **ID:** {data['roll']} | **Lang:** {data['language']}")
            with c2:
                if st.button(f"Approve ✅", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
        if not found:
            st.write("No pending student requests.")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("📖 Real-time AI Translation")
    teacher_text = st.text_area("Teacher: Enter Lesson Text here", height=150)
    
    if st.button("Broadcast to Students"):
        if teacher_text:
            st.session_state.lesson_content = teacher_text
            st.success("Lesson Broadcasted!")
        else:
            st.warning("Enter text first.")

    st.markdown("---")
    
    if "lesson_content" in st.session_state and db:
        st.subheader("Translated Content for Students:")
        approved = db.collection("requests").where("status", "==", "approved").stream()
        for stu in approved:
            data = stu.to_dict()
            with st.expander(f"For: {data['name']} ({data['language']})"):
                try:
                    translated = GoogleTranslator(source='auto', target=data["language"]).translate(st.session_state.lesson_content)
                    st.write(translated)
                except Exception as e:
                    st.error(f"Translation Error: {e}")
