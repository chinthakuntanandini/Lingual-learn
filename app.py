import streamlit as st
import ml_logic
import time

# Page Configuration
st.set_page_config(page_title="LinguaLearn AI Classroom", layout="wide")

# Custom CSS for Teacher and Student UI Styling
st.markdown("""
    <style>
    .teacher-box { background-color: #e3f2fd; padding: 20px; border-radius: 15px; border-left: 5px solid #1976d2; }
    .student-box { background-color: #f1f8e9; padding: 20px; border-radius: 15px; border-left: 5px solid #388e3c; }
    .stButton>button { width: 100%; background-color: #1976d2; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 LinguaLearn AI Classroom")
st.write("Real-time Teacher-Student Interaction Hub")

# Layout: Creating two functional columns
col1, col2 = st.columns(2)

with col1:
    # Teacher Interface Section
    st.markdown('<div class="teacher-box"><h3>👨‍🏫 Teacher Panel</h3></div>', unsafe_allow_html=True)
    st.write("Input lecture content (Speech-to-Text Simulation):")
    lecture_text = st.text_area("", height=200, placeholder="Type lesson here...", key="teacher_input")
    
    # Button to trigger AI analysis and broadcast content
    broadcast = st.button("📡 Broadcast to Students")

with col2:
    # Student Interface Section
    st.markdown('<div class="student-box"><h3>📖 Student View</h3></div>', unsafe_allow_html=True)
    
    if broadcast and lecture_text:
        # Visual indicator for data processing
        status = st.empty()
        status.info("Teacher is broadcasting... AI is analyzing the content.")
        time.sleep(1) # Simulating network/processing delay
        status.empty()

        # Execute AI logic from ml_logic.py
        subject, latency = ml_logic.process_ai(lecture_text)
        
        # Display the output to students
        st.subheader(f"Identified Topic: {subject}")
        st.markdown(f"**Lecture Notes:**\n\n{lecture_text}")
        
        # Sidebar: Technical metrics for evaluation
        st.sidebar.success("✅ AI Engine Processed Successfully")
        st.sidebar.metric("Prediction Latency", f"{latency} sec")
        st.sidebar.write(f"Algorithm: Random Forest & Linear Regression")
        
    else:
        st.write("Waiting for the teacher to start the session...")

st.markdown("---")
st.caption("Developed by Nandini | LinguaLearn AI Engine")
