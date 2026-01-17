"""
Configuration file for TTA Reconciliation System
API Key will be read from Streamlit Secrets only
"""

# API Configuration
# Read API Key from Streamlit Secrets
try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = None

# Folder Paths
PDF_FOLDER = "./data/agreements"
AP_FOLDER = "./data/ap"
AR_FOLDER = "./data/ar"
OUTPUT_FOLDER = "./data/output"
TEMP_FOLDER = "./data/temp"

# Application Settings
APP_TITLE = "TTA Reconciliation System"
APP_ICON = "📊"
PAGE_LAYOUT = "wide"

# Gemini API Settings
GEMINI_MODEL = "gemini-1.5-flash"

# File Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_CSV_EXTENSIONS = ['.csv']
ALLOWED_EXCEL_EXTENSIONS = ['.xlsx', '.xls']

# Analysis Settings
VARIANCE_THRESHOLD = 1.0
HIGH_VARIANCE_THRESHOLD = 10.0

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
