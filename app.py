import streamlit as st
import pandas as pd
from fpdf import FPDF
from deep_translator import GoogleTranslator

# --- PDF GENERATOR FUNCTION ---
def create_custom_pdf(title, header, rows):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    # Header
    pdf.set_font("Arial", 'B', 10)
    for col in header:
        pdf.cell(45, 10, txt=col, border=1)
    pdf.ln()
    
    # Data
    pdf.set_font("Arial", size=10)
    for row in rows:
        for item in row:
            pdf.cell(45, 10, txt=str(item), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 7. MODULE: AI REPORTS & DISTRIBUTION ---
if page == "AI Table Creator":
    st.header("📊 Teacher Report Control Panel")
    
    # Data Simulation (Idhi Firestore nunchi vachinattu imagine chey)
    report_data = [
        ["Nandini", "High", "Telugu", "Present"],
        ["Kumar", "Medium", "English", "Present"],
        ["Sita", "High", "Hindi", "Present"]
    ]
    columns = ["Student", "Engagement", "Language", "Status"]
    
    st.subheader("1. Class Summary Verification (English First)")
    summary_text = st.text_area("Review Class Summary (English):", 
                               "Today's class covered Neural Networks and Cloud Integration.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Verify & Send Summary to Students"):
            st.success("Summary translated to student languages and sent via NeuralBridge Cloud!")
            # Logic: Teacher approve chesaka students ki veltundi
            for row in report_data:
                student_lang = row[2].lower()[:2] # te, hi, etc.
                translated_summary = GoogleTranslator(source='en', target=student_lang).translate(summary_summary)
                # Idhi database lo 'student_reports' collection loki veltundi

    st.divider()
    
    st.subheader("2. Attendance Management")
    st.table(pd.DataFrame(report_data, columns=columns))
    
    if st.button("📋 Finalize & Send Attendance PDF to All"):
        # Attendance Report Creation
        att_rows = [[r[0], r[3]] for r in report_data]
        att_pdf = create_custom_pdf("Final Attendance Report", ["Student Name", "Status"], att_rows)
        
        st.download_button(
            label="📥 Download & Share Attendance",
            data=att_pdf,
            file_name="Final_Attendance.pdf",
            mime="application/pdf"
        )
        st.success("Attendance PDF generated and shared with the classroom!")
