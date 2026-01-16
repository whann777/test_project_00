"""
Configuration file for TTA Reconciliation System
"""

# Application Settings
APP_TITLE = "TTA Reconciliation System"
APP_ICON = "📊"

# Gemini API Settings
GEMINI_MODEL = "gemini-2.5-flash"

# File Upload Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_PDF_EXTENSIONS = ['pdf']
ALLOWED_CSV_EXTENSIONS = ['csv']
ALLOWED_EXCEL_EXTENSIONS = ['xlsx', 'xls']

# Analysis Settings
VARIANCE_THRESHOLD = 1.0  # บาท - ส่วนต่างที่ถือว่าเท่ากับ 0
HIGH_VARIANCE_THRESHOLD = 10.0  # เปอร์เซ็นต์ - ถือว่า variance สูง

# Export Settings
EXPORT_DATE_FORMAT = "%Y%m%d_%H%M%S"
EXCEL_ENGINE = "openpyxl"

# Display Settings
CURRENCY_FORMAT = "฿{:,.2f}"
PERCENT_FORMAT = "{:.2f}%"
LARGE_NUMBER_FORMAT = "{:,.0f}"

# Status Icons
STATUS_COMPLETE = "✅ ครบ"
STATUS_OVER = "⚠️ เกิน"
STATUS_UNDER = "❌ ขาด"

# Colors for Charts
COLOR_PRIMARY = "#2196F3"
COLOR_SUCCESS = "#4CAF50"
COLOR_WARNING = "#FFC107"
COLOR_DANGER = "#F44336"
COLOR_INFO = "#00BCD4"

# Temporary Directory
TEMP_DIR = "/tmp/tta_docs"

# Session State Keys
SESSION_MODE = "mode"
SESSION_ANALYSIS_RESULTS = "analysis_results"
SESSION_TEMP_DIR = "temp_dir"
SESSION_RECON_SYSTEM = "reconciliation_system"
SESSION_AUDITOR_DATA = "auditor_data"
