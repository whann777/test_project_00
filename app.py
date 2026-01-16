import streamlit as st
import os

# ตั้งค่าหน้า Page
st.set_page_config(
    page_title="TTA Reconciliation System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS สำหรับตกแต่ง
st.markdown("""
    <style>
    .main-header {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 20px;
        text-align: center;
        color: #666;
        margin-bottom: 50px;
    }
    .card {
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
        transition: transform 0.3s;
        cursor: pointer;
        background: white;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .card-analyze {
        border-left: 5px solid #4CAF50;
    }
    .card-auditor {
        border-left: 5px solid #2196F3;
    }
    .card-title {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .card-description {
        font-size: 16px;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">📊 TTA Reconciliation System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ระบบวิเคราะห์และตรวจสอบสัญญาการค้า</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # เลือกโหมด
    st.markdown("### 🎯 เลือกโหมดการใช้งาน")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card card-analyze">
            <div class="card-title">🔍 For Analyze</div>
            <div class="card-description">
                วิเคราะห์เอกสาร Agreement Contract พร้อมคำนวณและเปรียบเทียบกับยอดจริง
                <br><br>
                <b>ฟีเจอร์:</b>
                <ul>
                    <li>อัปโหลดและวิเคราะห์เอกสาร PDF</li>
                    <li>คำนวณ Allowances ตาม TTA</li>
                    <li>เปรียบเทียบกับยอดซื้อ (AP) และยอดเรียกเก็บ (AR)</li>
                    <li>Export ผลลัพธ์เป็น Excel</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 เข้าสู่โหมด Analyze", key="btn_analyze", use_container_width=True):
            st.session_state.mode = "analyze"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="card card-auditor">
            <div class="card-title">📋 For Auditor</div>
            <div class="card-description">
                ดูและตรวจสอบผลการวิเคราะห์ พร้อม Dashboard สรุปข้อมูล
                <br><br>
                <b>ฟีเจอร์:</b>
                <ul>
                    <li>Dashboard สรุปภาพรวม</li>
                    <li>กรองและค้นหาข้อมูลตาม Vendor</li>
                    <li>ดูรายละเอียดแต่ละ Vendor</li>
                    <li>Export ข้อมูลเป็น Excel/CSV</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 เข้าสู่โหมด Auditor", key="btn_auditor", use_container_width=True):
            st.session_state.mode = "auditor"
            st.rerun()
    
    st.markdown("---")
    
    # ข้อมูลเพิ่มเติม
    with st.expander("ℹ️ เกี่ยวกับระบบ"):
        st.markdown("""
        ### TTA Reconciliation System
        
        ระบบนี้ถูกพัฒนาขึ้นเพื่อช่วยในการวิเคราะห์และตรวจสอบสัญญาการค้า (Trade Terms Agreement) 
        ระหว่างห้างกับ Supplier แต่ละเจ้า โดยใช้ AI (Google Gemini) ในการอ่านและสรุปเอกสาร
        
        **ขั้นตอนการทำงาน:**
        1. วิเคราะห์เอกสาร PDF ด้วย AI
        2. สกัดข้อมูล Allowance แต่ละประเภท
        3. คำนวณยอดที่ควรเรียกเก็บตามยอดซื้อจริง
        4. เปรียบเทียบกับยอดที่เรียกเก็บจริง (AR)
        5. สรุปผลและ Export รายงาน
        
        **Allowance Categories ที่รองรับ:**
        - ARB: Unconditional Rebate
        - CRB: Conditional Rebate
        - BRO: Brochure Fee
        - ADP: Display Fee
        - MMF: Merchandise Marketing Fund
        - และอื่นๆ อีกมากมาย
        """)

if __name__ == "__main__":
    # Initialize session state
    if 'mode' not in st.session_state:
        st.session_state.mode = None
    
    # เช็คว่าเลือกโหมดแล้วหรือยัง
    if st.session_state.mode == "analyze":
        # เรียกหน้า Analyze
        import analyze_page
        analyze_page.show()
    elif st.session_state.mode == "auditor":
        # เรียกหน้า Auditor
        import auditor_page
        auditor_page.show()
    else:
        # แสดงหน้าเลือกโหมด
        main()
