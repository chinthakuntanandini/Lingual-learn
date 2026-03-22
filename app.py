import streamlit as st
from deep_translator import GoogleTranslator
from google.cloud import firestore
from google.oauth2 import service_account

# --- 1. FIREBASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            st.error("Firebase secrets not found!")
            return None
        
        firebase_info = dict(st.secrets["firebase"])
        # Handling the private key formatting
        raw_key = firebase_info["private_key"]
        private_key = raw_key.replace("\\n", "\n").strip().strip('"')
        firebase_info["private_key"] = private_key

        creds = service_account.Credentials.from_service_account_info(firebase_info)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Firebase Error: {e}")
        return None

db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", page_icon="🎓")
st.title("🎓 NeuralBridge: AI Smart Classroom")

# Sidebar Navigation
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

# Language Options
lang_options = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("👤 Student Registration")
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    lang_display = st.selectbox("Select Your Language", list(lang_options.keys()))
    lang_code = lang_options[lang_display]

    if st.button("Join Class"):
        if db and name and roll:
            db.collection("requests").document(roll).set({
                "name": name,
                "roll": roll,
                "language": lang_code,
                "status": "pending"
            })
            st.success("Registration Successful! Wait for approval.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Approval Panel")
    if db:
        requests = db.collection("requests").where("status", "==", "pending").stream()
        for doc in requests:
            data = doc.to_dict()
            st.write(f"Student: {data['name']} ({data['language']})")
            if st.button(f"Approve {data['roll']}", key=doc.id):
                db.collection("requests").document(doc.id).update({"status": "approved"})
                st.rerun()

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("📖 Real-time Translation")
    teacher_text = st.text_area("Teacher: Enter Text")
    
    if st.button("Broadcast"):
        st.session_state.content = teacher_text
        st.success("Sent!")

    if "content" in st.session_state and db:
        approved = db.collection("requests").where("status", "==", "approved").stream()
        for stu in approved:
            data = stu.to_dict()
            translated = GoogleTranslator(source='auto', target=data["language"]).translate(st.session_state.content)
            st.info(f"**For {data['name']} ({data['language']}):** {translated}")
