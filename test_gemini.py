# test_gemini.py
import google.generativeai as genai

# ทดสอบ API Key
API_KEY = "AIzaSyBfd3VWbYXOCgfnegrn8wuQ0pX8OONjlXg"
genai.configure(api_key=API_KEY)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello, test API")
    print("✅ API Key ใช้งานได้!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ API Key ไม่ทำงาน: {e}")
