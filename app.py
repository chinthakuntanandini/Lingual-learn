import streamlit as st
import ml_logic  # Importing the custom ML logic file to link the models

# Page Configuration for the Streamlit Web App
st.set_page_config(page_title="LinguaLearn AI", layout="centered")

st.title("🎓 LinguaLearn AI Classroom")
st.write("Real-time Speech Analysis and Categorization using Machine Learning")

# 1. Input Section: This is where the teacher's captured speech or text arrives
# Note: If using Speech-to-Text API, the output string should be passed here
teacher_text = st.text_area("Teacher's Speech / Lecture Content:", placeholder="Type or paste the lecture text here...")

if st.button("Process with AI"):
    if teacher_text:
        # --- ML Logic Connection Start ---
        
        # Calling the process_ai function from ml_logic.py
        # This triggers both Classification and Regression models
        subject, time_pred = ml_logic.process_ai(teacher_text)
        
        # --- ML Logic Connection End ---

        # UI Layout: Displaying the AI Analysis results
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Displaying the Classification result (Random Forest)
            st.subheader("📌 Classification")
            st.success(f"**Detected Subject:** {subject}")
            st.caption("Categorized using Random Forest Algorithm")

        with col2:
            # Displaying the Regression result (Linear Regression)
            st.subheader("⏳ Performance (Regression)")
            st.info(f"**Estimated Latency:** {time_pred} sec")
            st.caption("Predicted using Linear Regression")

        # Section to display the actual text content processed
        st.write("---")
        st.subheader("📝 Processed Content")
        st.write(teacher_text)
        
    else:
        st.warning("Please enter some text to analyze.")

# Sidebar documentation for the Guide/Examiner
st.sidebar.markdown("""
### **Custom AI/ML Features:**
- **Classification:** Uses a trained Random Forest model to identify the subject.
- **Regression:** Uses Linear Regression to predict system processing delay.
- **Clustering:** Internal logic (K-Means) is used for thematic grouping of notes.
""")
