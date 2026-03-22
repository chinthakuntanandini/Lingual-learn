import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

# --- SECURE FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    try:
        if "firebase" in st.secrets:
            # Secrets ని డిక్షనరీ లోకి తీసుకోవడం
            info = dict(st.secrets["firebase"])
            
            # కీ లో ఉన్న స్లాష్ లని సరిచేయడం (PEM Error Fix)
            if "private_key" in info:
                # Replace double backslashes and ensure correct newline formatting
                info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            
            # Authenticating with Google Cloud
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        # If any error occurs, it will be displayed here
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()
