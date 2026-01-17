import streamlit as st
import config

st.title("🔑 ทดสอบ Gemini API Key")

st.write("### ตรวจสอบการตั้งค่า")

# แสดง API Key (ซ่อนส่วนกลาง)
api_key = config.GEMINI_API_KEY
if api_key and api_key != "AIzaSyBfd3VWbYXOCgfnegrn8wuQ0pX8OONjlXg":
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    st.success(f"✅ พบ API Key: {masked_key}")
else:
    st.error("❌ ยังไม่ได้ตั้งค่า API Key ในไฟล์ config.py")
    st.stop()

# ทดสอบ API
if st.button("🧪 ทดสอบ API Key"):
    with st.spinner("กำลังทดสอบ..."):
        try:
            import google.generativeai as genai
            
            # Configure
            genai.configure(api_key=api_key)
            
            # ทดสอบเรียก API
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Say hello")
            
            st.success("✅ API Key ใช้งานได้!")
            st.write("**Response:**", response.text)
            
        except Exception as e:
            st.error(f"❌ API Key ไม่สามารถใช้งานได้")
            st.write("**Error Type:**", type(e).__name__)
            st.write("**Error Message:**", str(e))
            
            if "API_KEY_INVALID" in str(e) or "invalid" in str(e).lower():
                st.warning("💡 API Key ไม่ถูกต้อง - กรุณาสร้าง API Key ใหม่")
                st.write("ขอ API Key ใหม่ได้ที่: https://aistudio.google.com/app/apikey")
            
            import traceback
            with st.expander("📋 รายละเอียด Error"):
                st.code(traceback.format_exc())

st.write("---")
st.write("### 📝 วิธีแก้ไข")
st.write("""
1. ไปที่: https://aistudio.google.com/app/apikey
2. คลิก "Create API Key"
3. Copy API Key
4. เปิดไฟล์ `config.py`
5. แก้ไขบรรทัด: `GEMINI_API_KEY = "วาง_API_Key_ที่นี่"`
6. Save และ Push ไป GitHub
7. รอ Streamlit Cloud restart
""")
