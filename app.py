import streamlit as st
import os
from pathlib import Path
import config

# ตั้งค่าหน้า Page
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.PAGE_LAYOUT,
    initial_sidebar_state="expanded"
)

# Modern CSS Styling
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: #F5F7FA;
        border-radius: 20px;
        margin-top: 1rem;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 3rem 0 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .main-subtitle {
        font-size: 1.3rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Card styling */
    .mode-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
        position: relative;
        overflow: hidden;
    }
    
    .mode-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .mode-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    .card-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .card-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2D3748;
        margin-bottom: 0.8rem;
    }
    
    .card-description {
        font-size: 1rem;
        color: #718096;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    
    .feature-list {
        list-style: none;
        padding: 0;
        margin: 1rem 0;
    }
    
    .feature-list li {
        padding: 0.5rem 0;
        color: #4A5568;
        font-size: 0.95rem;
    }
    
    .feature-list li::before {
        content: "✓";
        color: #43A047;
        font-weight: bold;
        margin-right: 0.8rem;
        font-size: 1.2rem;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Info box */
    .info-box {
        background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
    }
    
    .info-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.5rem;
    }
    
    .info-content {
        color: #1e3a8a;
        line-height: 1.6;
    }
    
    /* Stats styling */
    .stat-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    
    .stat-box {
        text-align: center;
        padding: 1.5rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: white;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        .card-title {
            font-size: 1.4rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

def check_folders():
    """ตรวจสอบและสร้างโฟลเดอร์ที่จำเป็น"""
    folders = [
        config.PDF_FOLDER,
        config.AP_FOLDER,
        config.AR_FOLDER,
        config.OUTPUT_FOLDER,
        config.TEMP_FOLDER
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)

def main():
    # ตรวจสอบ API Key
    if config.GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        st.error("⚠️ กรุณาใส่ Google Gemini API Key ในไฟล์ config.py")
        st.info("""
        **วิธีการตั้งค่า:**
        1. เปิดไฟล์ `config.py`
        2. แก้ไขบรรทัด `GEMINI_API_KEY = "YOUR_API_KEY_HERE"`
        3. ใส่ API Key ของคุณแทน
        4. บันทึกไฟล์และ refresh หน้านี้
        
        **ขอ API Key ได้ที่:** https://aistudio.google.com/app/apikey
        """)
        return
    
    # สร้างโฟลเดอร์
    check_folders()
    
    # Header
    st.markdown("""
        <div class="main-header">
            <div class="main-title">📊 TTA Reconciliation System</div>
            <div class="main-subtitle">ระบบวิเคราะห์และตรวจสอบสัญญาการค้าอัตโนมัติ</div>
        </div>
    """, unsafe_allow_html=True)
    
    # เลือกโหมด
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div class="mode-card">
            <span class="card-icon">🔍</span>
            <div class="card-title">Analysis Mode</div>
            <div class="card-description">
                วิเคราะห์เอกสารและคำนวณอัตโนมัติ
            </div>
            <ul class="feature-list">
                <li>วิเคราะห์ PDF ทั้งโฟลเดอร์อัตโนมัติ</li>
                <li>คำนวณ Allowances จากยอดซื้อ</li>
                <li>เปรียบเทียบกับยอดเรียกเก็บจริง</li>
                <li>สร้างรายงานสรุปแบบ Real-time</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 เริ่ม Analysis", key="btn_analyze", use_container_width=True):
            st.session_state.mode = "analyze"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="mode-card">
            <span class="card-icon">📋</span>
            <div class="card-title">Dashboard Mode</div>
            <div class="card-description">
                ดูและตรวจสอบผลการวิเคราะห์
            </div>
            <ul class="feature-list">
                <li>Dashboard แสดงผลแบบ Interactive</li>
                <li>วิเคราะห์เชิงลึกและ Visualization</li>
                <li>กรองและค้นหาข้อมูลตาม Vendor</li>
                <li>Export รายงานหลายรูปแบบ</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 เปิด Dashboard", key="btn_auditor", use_container_width=True):
            st.session_state.mode = "auditor"
            st.rerun()
    
    # Info section
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("ℹ️ ข้อมูลเพิ่มเติมและการตั้งค่า", expanded=False):
        st.markdown("""
        ### 📁 โครงสร้างโฟลเดอร์
        
        ระบบจะอ่านไฟล์จากโฟลเดอร์ดังนี้:
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.code(f"""
📂 {config.PDF_FOLDER}
   └── ไฟล์ Agreement PDF

📂 {config.AP_FOLDER}
   └── ไฟล์ AP CSV
            """)
        
        with col2:
            st.code(f"""
📂 {config.AR_FOLDER}
   └── ไฟล์ AR CSV

📂 {config.OUTPUT_FOLDER}
   └── ไฟล์ผลลัพธ์
            """)
        
        st.markdown("""
        ### ⚙️ การตั้งค่า
        
        แก้ไขได้ที่ไฟล์ **config.py**:
        - `GEMINI_API_KEY`: API Key สำหรับ Gemini AI
        - `PDF_FOLDER`: โฟลเดอร์เก็บไฟล์ PDF
        - `AP_FOLDER`: โฟลเดอร์เก็บไฟล์ AP
        - `AR_FOLDER`: โฟลเดอร์เก็บไฟล์ AR
        - `OUTPUT_FOLDER`: โฟลเดอร์เก็บผลลัพธ์
        
        ### 📊 Allowance Categories ที่รองรับ
        
        ระบบรองรับ 22 หมวดหมู่ เช่น ARB, CRB, BRO, MMF, GCS, etc.
        
        ### 🔒 ความปลอดภัย
        
        - API Key เก็บในไฟล์ config.py (อย่า commit ลง Git)
        - ข้อมูลทั้งหมดประมวลผลใน Local
        - ไม่มีการส่งข้อมูลออกนอกระบบ
        """)

if __name__ == "__main__":
    # Initialize session state
    if 'mode' not in st.session_state:
        st.session_state.mode = None
    
    # เช็คว่าเลือกโหมดแล้วหรือยัง
    if st.session_state.mode == "analyze":
        import analyze_page
        analyze_page.show()
    elif st.session_state.mode == "auditor":
        import auditor_page
        auditor_page.show()
    else:
        main()
