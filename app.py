import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json

# --- 1. FIREBASE CONNECTION SETTINGS (UPDATED) ---
@st.cache_resource
def init_connection():
    try:
        # Streamlit Secrets నుండి వివరాలను డిక్షనరీగా తీసుకోవడం
        firebase_info = st.secrets["firebase"]
        
        # కీ లో ఉన్న కొత్త లైన్ (\n) సమస్యను సరిచేయడం
        # ఇది PEM ఫైల్ ఎర్రర్ రాకుండా చూస్తుంది
        key_content = firebase_info["private_key"].replace("\\n", "\n")
        
        # కనెక్షన్ వివరాలను సిద్ధం చేయడం
        creds_dict = {
            "type": firebase_info["type"],
            "project_id": firebase_info["project_id"],
            "private_key_id": firebase_info["private_key_id"],
            "private_key": key_content,
            "client_email": firebase_info["client_email"],
            "client_id": firebase_info["client_id"],
            "auth_uri": firebase_info["auth_uri"],
            "token_uri": firebase_info["token_uri"],
            "auth_provider_x509_cert_url": firebase_info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_info["client_x509_cert_url"],
        }
        
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        return None

# డేటాబేస్ ఇనిషియలైజేషన్
db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")

# Sidebar Navigation
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: Multi-Device AI Smart Class")

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Your Name")
    roll = st.text_input("Enter Roll Number")
    lang = st.selectbox("Select Your Language", ["Telugu", "Hindi", "English", "Tamil"])

    if st.button("Register & Join"):
        if db is None:
            st.error("Database connection failed. Check your Secrets.")
        elif name and roll:
            try:
                # Firestore లో డేటా సేవ్ చేయడం
                db.collection("requests").document(roll).set({
                    "name": name,
                    "roll": roll,
                    "language": lang,
                    "status": "pending"
                })
                st.success(f"Hello {name}, your request sent to Teacher. Please wait for approval!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
        else:
            st.warning("Please enter both Name and Roll Number")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    
    if db is None:
        st.error("Database connection failed. Check your Secrets.")
    else:
        try:
            # Pending రిక్వెస్ట్‌లను చూపించడం
            requests_ref = db.collection("requests").where("status", "==", "pending").stream()
            
            # రిక్వెస్ట్‌లు ఉన్నాయో లేదో చూడటానికి
            has_requests = False
            for doc in requests_ref:
                has_requests = True
                data = doc.to_dict()
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{data['name']}** ({data['roll']}) - {data['language']}")
                with col2:
                    if st.button("Approve", key=doc.id):
                        db.collection("requests").document(doc.id).update({"status": "approved"})
                        st.rerun()
            
            if not has_requests:
                st.info("No pending requests at the moment.")
                
        except Exception as e:
            st.error(f"Error fetching data: {e}")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("Live Interactive Session")
    st.write("Translation and Voice features will load here...")
