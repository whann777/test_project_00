"""
Configuration file for TTA Reconciliation System
API Key จะอ่านจาก Streamlit Secrets เท่านั้น
"""

import streamlit as st

# ===== API Configuration =====
# อ่าน API Key จาก Streamlit Secrets
# ตั้งค่าใน Streamlit Cloud: Settings > Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception as e:
    # ถ้าไม่เจอ API Key จะแจ้งเตือนให้ตั้งค่า
    GEMINI_API_KEY = None

# ===== Folder Paths =====
# กำหนด path ของโฟลเดอร์ที่เก็บไฟล์
PDF_FOLDER = "./data/agreements"      # โฟลเดอร์ที่เก็บไฟล์ PDF Agreement Contract
AP_FOLDER = "./data/ap"                # โฟลเดอร์ที่เก็บไฟล์ AP CSV
AR_FOLDER = "./data/ar"                # โฟลเดอร์ที่เก็บไฟล์ AR CSV
OUTPUT_FOLDER = "./data/output"        # โฟลเดอร์สำหรับเก็บผลลัพธ์
TEMP_FOLDER = "./data/temp"            # โฟลเดอร์ temp

# ===== Application Settings =====
APP_TITLE = "TTA Reconciliation System"
APP_ICON = "📊"
PAGE_LAYOUT = "wide"

# Gemini API Settings
GEMINI_MODEL = "gemini-2.5-flash"

# File Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_CSV_EXTENSIONS = ['.csv']
ALLOWED_EXCEL_EXTENSIONS = ['.xlsx', '.xls']

# Analysis Settings
VARIANCE_THRESHOLD = 1.0  # บาท
HIGH_VARIANCE_THRESHOLD = 10.0  # %

# Export Settings
EXPORT_DATE_FORMAT = "%Y%m%d_%H%M%S"
EXCEL_ENGINE = "openpyxl"

# Display Settings
CURRENCY_FORMAT = "฿{:,.2f}"
PERCENT_FORMAT = "{:.2f}%"
LARGE_NUMBER_FORMAT = "{:,.0f}"

# Status Icons and Colors
STATUS_COMPLETE = "✅ ครบ"
STATUS_OVER = "⚠️ เกิน"
STATUS_UNDER = "❌ ขาด"

# Chart Colors
COLOR_PRIMARY = "#1E88E5"
COLOR_SUCCESS = "#43A047"
COLOR_WARNING = "#FB8C00"
COLOR_DANGER = "#E53935"
COLOR_INFO = "#00ACC1"
COLOR_BACKGROUND = "#F5F7FA"
COLOR_CARD = "#FFFFFF"

# Session State Keys
SESSION_MODE = "mode"
SESSION_ANALYSIS_RESULTS = "analysis_results"
SESSION_RECON_SYSTEM = "reconciliation_system"
SESSION_AUDITOR_DATA = "auditor_data"
SESSION_PROCESSING_DONE = "processing_done"
