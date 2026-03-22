import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

# --- SECURE FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    """
    Rectifies formatting errors in the RSA Private Key and 
    establishes a secure connection to Firestore.
    """
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            
            if "private_key" in info:
                # FIX: Rectifying the literal string to actual newline characters
                info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        # Error rectification feedback
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()
