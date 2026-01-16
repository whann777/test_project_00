"""
TTA Analysis Streamlit App
วิเคราะห์เอกสาร TTA ด้วย AI และทำ Reconciliation

วิธีติดตั้ง:
pip install streamlit google-generativeai pandas openpyxl pillow pdf2image

วิธีรัน:
streamlit run app.py
"""

import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from typing import Dict, List
import time
from datetime import datetime
import io

# ========================================
# Configuration
# ========================================

st.set_page_config(
    page_title="TTA Analysis System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# Constants
# ========================================

ALLOWANCE_CATEGORIES = {
    "ARB": "Unconditional Rebate",
    "CRB": "Conditional Rebate",
    "BRO": "Brochure Fee",
    "ADP": "Display Fee",
    "MMF": "Merchandise Marketing Fund",
    "SEN": "Seasonal Support",
    "COF": "Cooperate Coupon Support",
    "ANI": "Anniversary Discount",
    "OTS": "Other Promotion Service",
    "OTN": "Other Promotion Support",
    "DTS": "Data Sharing Fee",
    "NRT": "Non Return Discount",
    "HQC": "Hygiene & Quality Control",
    "GCS": "Guarantee GP Compensation",
    "P13": "Training Support",
    "NIT": "New Item Support",
    "NST": "New Store Opening",
    "RST": "Store Renovate",
    "PCM": "PC Missing Fee",
    "WPS": "Vendor Web Portal Service",
    "OTH": "Others Allowance",
    "SPD": "Special Discount",
    "CCS": "Clearance/Markdown"
}

# ========================================
# Helper Classes (จากโค้ดเดิม)
# ========================================

class DataPreprocessor:
    """ทำความสะอาดและเตรียมข้อมูล AP และ AR"""
    
    @staticmethod
    def clean_amount(value):
        """ทำความสะอาดตัวเลขจำนวนเงิน"""
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        
        value_str = str(value).strip().replace(',', '').replace(' ', '')
        
        is_negative = False
        if value_str.startswith('(') and value_str.endswith(')'):
            is_negative = True
            value_str = value_str[1:-1]
        
        value_str = value_str.replace('฿', '').replace('$', '').replace('THB', '')
        
        try:
            result = float(value_str)
            return -result if is_negative else result
        except:
            return 0.0
    
    @staticmethod
    def prepare_ap_data(df: pd.DataFrame) -> pd.DataFrame:
        """เตรียมข้อมูล AP (Purchase/Account Payable)"""
        df = df.copy()
        
        if 'INVPAYAMT' in df.columns:
            df['INVPAYAMT'] = df['INVPAYAMT'].apply(DataPreprocessor.clean_amount)
        if 'INV_AMOUNT' in df.columns:
            df['INV_AMOUNT'] = df['INV_AMOUNT'].apply(DataPreprocessor.clean_amount)
        
        if 'VndCode' in df.columns:
            df['VndCode'] = df['VndCode'].astype(str).str.replace('.0', '').str.strip()
        
        if 'DEPT_CODE' in df.columns:
            df['DEPT_CODE_ORIGINAL'] = df['DEPT_CODE'].astype(str)
            df['DEPT_CODE_STR'] = df['DEPT_CODE'].astype(str).str.zfill(4)
            df['DIV_CODE'] = df['DEPT_CODE_STR'].str[:2]
            df['DEPT_CODE_FINAL'] = df['DEPT_CODE_STR'].str[2:]
        
        df['VENDOR_KEY'] = df['VndCode'].astype(str)
        df['TTA_MATCH_KEY'] = (df['VndCode'].astype(str) + '_' + 
                               df['DIV_CODE'] + '_' + 
                               df['DEPT_CODE_FINAL'])
        
        if 'INV_YEAR' in df.columns:
            df['YEAR'] = df['INV_YEAR'].astype(int)
        
        return df
    
    @staticmethod
    def prepare_ar_data(df: pd.DataFrame) -> pd.DataFrame:
        """เตรียมข้อมูล AR (Account Receivable)"""
        df = df.copy()
        
        if 'EXTENDED_AMOUNT' in df.columns:
            df['EXTENDED_AMOUNT'] = df['EXTENDED_AMOUNT'].apply(DataPreprocessor.clean_amount)
        
        if 'SUP_CODE' in df.columns:
            df['SUP_CODE'] = df['SUP_CODE'].astype(str).str.replace('.0', '').str.strip()
        
        if 'DPTNBR' in df.columns:
            df['DPTNBR_STR'] = df['DPTNBR'].astype(str).str.replace('.0', '').str.zfill(4)
            df['DIV_CODE'] = df['DPTNBR_STR'].str[:2]
            df['DEPT_CODE'] = df['DPTNBR_STR'].str[2:]
        
        df['VENDOR_KEY'] = df['SUP_CODE'].astype(str)
        df['TTA_MATCH_KEY'] = (df['SUP_CODE'].astype(str) + '_' + 
                               df['DIV_CODE'] + '_' + 
                               df['DEPT_CODE'])
        
        if 'REF_TYPE' in df.columns:
            df['REF_TYPE_CLEAN'] = df['REF_TYPE'].str.upper().str.strip()
        else:
            df['REF_TYPE_CLEAN'] = ''
        
        if 'DESCRIPTION' in df.columns:
            df['DESCRIPTION_CLEAN'] = df['DESCRIPTION'].str.upper().str.strip()
        
        if 'Year' in df.columns:
            df['YEAR'] = df['Year'].fillna(0).astype(int)
        
        return df

class TTADocumentAnalyzer:
    """วิเคราะห์เอกสาร TTA ด้วย Gemini AI"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(self.model_name)
    
    def create_analysis_prompt(self) -> str:
        categories_text = "\n".join([f"- {code}: {name}" for code, name in ALLOWANCE_CATEGORIES.items()])
        
        prompt = f"""
คุณคือผู้เชี่ยวชาญด้านสัญญาการค้า (Trade Terms)
โปรดวิเคราะห์ไฟล์เอกสารแนบนี้ (PDF) ซึ่งเป็นข้อตกลงทางการค้า และดึงข้อมูลออกมาในรูปแบบ JSON:

1. หา Vendor Code, Division Code, Division Name, Department Code, Department Name จากเอกสาร
2. สกัดข้อมูล allowance แต่ละประเภทพร้อมเงื่อนไข โดยจัดหมวดหมู่ตามรายการนี้:

{categories_text}

สำหรับแต่ละ allowance ให้ระบุ:
- Category Code (จากรายการด้านบน)
- Category Name 
- Rate (% ถ้ามี)
- Fix Amount (จำนวนเงินคงที่ ถ้ามี)
- Description (รายละเอียดหรือเงื่อนไข)
- Payment Terms (เงื่อนไขการจ่าย เช่น monthly, quarterly, annually)

กฎการวิเคราะห์ (Extraction Rules):
1. สนใจเฉพาะส่วนที่มีหัวข้อชัดเจนเท่านั้น ไม่ต้องสนใจเนื้อหาในส่วน Others Agreement
2. หน้า 2 อาจจะมีทั้งส่วนที่มีหัวข้อชัดเจนและไม่ชัดเจน ให้วิเคราะห์หน้า 2 อย่างละเอียดโดยวิเคราะห์จากบริบทและเนื้อหา
3. ถ้าหน้า 2 ไม่มีหัวข้อชัดเจน ให้วิเคราะห์จากเนื้อหาและจัดกลุ่มให้ตรงกับหมวดหมู่ที่กำหนดไว้
4. ถ้ามีทั้ง Rate และ Fix Amount ให้ระบุทั้งสอง
5. สรุปเฉพาะหัวข้อที่มี Rate หรือ Fix Amount

Response ในรูปแบบ JSON เท่านั้น:
{{
  "vendor_code": "รหัสผู้ขาย",
  "Division_code": "รหัสแผนก",
  "Division_name": "ชื่อแผนก",
  "Department_code": "รหัสกลุ่ม",
  "Department_name": "ชื่อกลุ่ม",
  "allowances": [
    {{
      "category_code": "ARB",
      "category_name": "Unconditional Rebate",
      "rate_percent": 5.0,
      "fix_amount": null,
      "description": "รายละเอียดเงื่อนไข",
      "payment_terms": "monthly"
    }}
  ]
}}
"""
        return prompt
    
    def analyze_document(self, pdf_path: str) -> Dict:
        """วิเคราะห์เอกสารโดยใช้ Gemini File API"""
        try:
            doc_file = genai.upload_file(path=pdf_path, display_name="Trade_Term_Doc")
            
            while doc_file.state.name == "PROCESSING":
                time.sleep(2)
                doc_file = genai.get_file(doc_file.name)
            
            if doc_file.state.name == "FAILED":
                return {"error": "Google AI แปลงไฟล์ PDF ไม่สำเร็จ"}
            
            prompt = self.create_analysis_prompt()
            
            generation_config = {
                "temperature": 0.0,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            }
            
            response = self.model.generate_content(
                [prompt, doc_file],
                generation_config=generation_config
            )
            
            response_text = response.text.strip()
            return json.loads(response_text)
            
        except Exception as e:
            return {"error": str(e)}

class TTAReconciliationSystem:
    """ระบบคำนวณและเปรียบเทียบ Allowances"""
    
    def __init__(self):
        self.tta_data = {}
        self.ap_data = None
        self.ar_data = None
        self.calculated_allowances = None
        self.reconciliation_result = None
    
    def calculate_allowances(self) -> pd.DataFrame:
        """คำนวณ allowance ที่ควรได้"""
        if self.ap_data is None or not self.tta_data:
            return None
        
        results = []
        
        for idx, row in self.ap_data.iterrows():
            tta_key = row['TTA_MATCH_KEY']
            vendor_code = row['VndCode']
            vendor_name = row['VNDNAME']
            div_code = row['DIV_CODE']
            dept_code = row['DEPT_CODE_FINAL']
            purchase_amount = row['INVPAYAMT']
            year = row.get('YEAR', 2023)
            
            if tta_key not in self.tta_data:
                continue
            
            tta = self.tta_data[tta_key]
            allowances = tta.get('allowances', [])
            
            for allowance in allowances:
                category_code = allowance.get('category_code')
                category_name = allowance.get('category_name')
                rate_percent = allowance.get('rate_percent')
                fix_amount = allowance.get('fix_amount')
                description = allowance.get('description', '')
                payment_terms = allowance.get('payment_terms', '')
                
                calculated_amount = 0
                calculation_type = ''
                
                if rate_percent is not None and rate_percent > 0:
                    calculated_amount = purchase_amount * (float(rate_percent) / 100)
                    calculation_type = f'{rate_percent}%'
                elif fix_amount is not None and fix_amount > 0:
                    calculated_amount = float(fix_amount)
                    calculation_type = 'Fix Amount'
                else:
                    continue
                
                results.append({
                    'vendor_code': vendor_code,
                    'vendor_name': vendor_name,
                    'division': div_code,
                    'department': dept_code,
                    'tta_key': tta_key,
                    'year': year,
                    'purchase_amount': purchase_amount,
                    'category_code': category_code,
                    'category_name': category_name,
                    'rate_percent': rate_percent,
                    'fix_amount': fix_amount,
                    'calculated_amount': calculated_amount,
                    'calculation_type': calculation_type,
                    'description': description,
                    'payment_terms': payment_terms
                })
        
        if results:
            self.calculated_allowances = pd.DataFrame(results)
        else:
            self.calculated_allowances = pd.DataFrame()
        
        return self.calculated_allowances
    
    def reconcile_with_ar(self) -> pd.DataFrame:
        """เปรียบเทียบกับ AR โดยใช้ REF_TYPE"""
        if self.calculated_allowances is None or self.ar_data is None:
            return None
        
        reconciliation_results = []
        
        for tta_key, group in self.calculated_allowances.groupby('tta_key'):
            vendor_code = group['vendor_code'].iloc[0]
            vendor_name = group['vendor_name'].iloc[0]
            
            for _, calc_row in group.iterrows():
                category_code = calc_row['category_code']
                category_name = calc_row['category_name']
                should_collect = calc_row['calculated_amount']
                
                ar_match = self.ar_data[
                    (self.ar_data['TTA_MATCH_KEY'] == tta_key) & 
                    (self.ar_data['REF_TYPE_CLEAN'] == category_code)
                ]
                
                actually_collected = ar_match['EXTENDED_AMOUNT'].sum() if not ar_match.empty else 0
                difference = actually_collected - should_collect
                
                if abs(difference) < 1:
                    status = '✅ ครบ'
                elif difference > 0:
                    status = '⚠️ เกิน'
                else:
                    status = '❌ ขาด'
                
                reconciliation_results.append({
                    'tta_key': tta_key,
                    'vendor_code': vendor_code,
                    'vendor_name': vendor_name,
                    'category_code': category_code,
                    'category_name': category_name,
                    'should_collect': should_collect,
                    'actually_collected': actually_collected,
                    'difference': difference,
                    'status': status,
                    'variance_pct': (difference / should_collect * 100) if should_collect > 0 else 0
                })
        
        self.reconciliation_result = pd.DataFrame(reconciliation_results)
        return self.reconciliation_result
    
    def generate_summary_report(self) -> pd.DataFrame:
        """สร้างรายงานสรุป"""
        if self.reconciliation_result is None:
            return None
        
        summary = self.reconciliation_result.groupby(['vendor_code', 'vendor_name']).agg({
            'should_collect': 'sum',
            'actually_collected': 'sum',
            'difference': 'sum'
        }).reset_index()
        
        summary['status'] = summary['difference'].apply(
            lambda x: '✅ ครบ' if abs(x) < 1 else ('⚠️ เกิน' if x > 0 else '❌ ขาด')
        )
        
        summary['variance_pct'] = (
            summary['difference'] / summary['should_collect'] * 100
        ).round(2)
        
        return summary

# ========================================
# Session State Initialization
# ========================================

if 'tta_data' not in st.session_state:
    st.session_state.tta_data = {}

if 'ap_data' not in st.session_state:
    st.session_state.ap_data = None

if 'ar_data' not in st.session_state:
    st.session_state.ar_data = None

if 'calculated_allowances' not in st.session_state:
    st.session_state.calculated_allowances = None

if 'reconciliation_result' not in st.session_state:
    st.session_state.reconciliation_result = None

if 'summary_report' not in st.session_state:
    st.session_state.summary_report = None

# ========================================
# Sidebar
# ========================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="ใส่ API Key ของ Google Gemini"
    )
    
    st.markdown("---")
    st.header("📊 Status")
    
    st.metric("TTA Documents", len(st.session_state.tta_data))
    st.metric("AP Records", len(st.session_state.ap_data) if st.session_state.ap_data is not None else 0)
    st.metric("AR Records", len(st.session_state.ar_data) if st.session_state.ar_data is not None else 0)
    
    st.markdown("---")
    st.header("📋 Navigation")
    page = st.radio(
        "เลือกหน้า",
        ["🔍 Analyze TTA", "💰 Calculate & Reconcile", "📊 Query Data"]
    )

# ========================================
# Main App
# ========================================

st.title("📊 TTA Analysis & Reconciliation System")
st.markdown("---")

# ========================================
# Page 1: Analyze TTA
# ========================================

if page == "🔍 Analyze TTA":
    st.header("🔍 วิเคราะห์เอกสาร TTA")
    
    if not api_key:
        st.warning("⚠️ กรุณาใส่ Gemini API Key ใน Sidebar")
        st.stop()
    
    st.subheader("📤 อัพโหลดไฟล์ TTA")
    uploaded_files = st.file_uploader(
        "เลือกไฟล์ PDF (สามารถเลือกหลายไฟล์)",
        type=['pdf'],
        accept_multiple_files=True,
        help="อัพโหลดไฟล์ TTA ของแต่ละ Vendor"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ไฟล์ที่เลือก", len(uploaded_files) if uploaded_files else 0)
    with col2:
        st.metric("Vendors วิเคราะห์แล้ว", len(st.session_state.tta_data))
    
    if uploaded_files:
        if st.button("🚀 เริ่มวิเคราะห์ทั้งหมด", type="primary", use_container_width=True):
            temp_dir = Path("temp_tta")
            temp_dir.mkdir(exist_ok=True)
            
            analyzer = TTADocumentAnalyzer(api_key)
            
            progress_bar = st.progress(0)
            status_container = st.container()
            
            results = {}
            
            for idx, uploaded_file in enumerate(uploaded_files):
                with status_container:
                    st.info(f"📄 กำลังวิเคราะห์: {uploaded_file.name} ({idx+1}/{len(uploaded_files)})")
                
                temp_path = temp_dir / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                result = analyzer.analyze_document(str(temp_path))
                
                if "error" not in result:
                    vendor_code = result.get('vendor_code')
                    div_code = str(result.get('Division_code', '')).zfill(2)
                    dept_code = str(result.get('Department_code', '')).zfill(2)
                    key = f"{vendor_code}_{div_code}_{dept_code}"
                    
                    results[key] = {
                        **result,
                        'filename': uploaded_file.name,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
                    with status_container:
                        st.success(f"✅ {uploaded_file.name} - Key: {key}")
                else:
                    with status_container:
                        st.error(f"❌ {uploaded_file.name} - Error: {result['error']}")
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
                temp_path.unlink()
            
            st.session_state.tta_data.update(results)
            
            status_container.empty()
            progress_bar.empty()
            
            st.success(f"✅ วิเคราะห์เสร็จสิ้น! พบ {len(results)} vendors")
            st.balloons()
            time.sleep(2)
            st.rerun()
    
    if st.session_state.tta_data:
        st.markdown("---")
        st.subheader("📋 รายการ Vendors ที่วิเคราะห์แล้ว")
        
        for key, data in st.session_state.tta_data.items():
            with st.expander(f"**{key}** - {data.get('filename', 'N/A')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**ข้อมูล Vendor:**")
                    st.write(f"- Vendor Code: `{data.get('vendor_code')}`")
                    st.write(f"- Division: `{data.get('Division_code')}` - {data.get('Division_name')}")
                    st.write(f"- Department: `{data.get('Department_code')}` - {data.get('Department_name')}")
                    st.write(f"- Analyzed: {data.get('analyzed_at', 'N/A')}")
                
                with col2:
                    allowances = data.get('allowances', [])
                    st.metric("Allowances", len(allowances))
                    
                    if st.button("🗑️ ลบ", key=f"del_{key}"):
                        del st.session_state.tta_data[key]
                        st.rerun()
                
                if allowances:
                    st.write("**Allowances:**")
                    df_allow = pd.DataFrame(allowances)
                    st.dataframe(df_allow[['category_code', 'category_name', 'rate_percent', 'fix_amount']], use_container_width=True)

# ========================================
# Page 2: Calculate & Reconcile
# ========================================

elif page == "💰 Calculate & Reconcile":
    st.header("💰 คำนวณและเปรียบเทียบ")
    
    if not st.session_state.tta_data:
        st.warning("⚠️ กรุณาวิเคราะห์เอกสาร TTA ก่อน")
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "🧮 Calculate", "📊 Results"])
    
    with tab1:
        st.subheader("📤 อัพโหลดข้อมูล AP และ AR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**ข้อมูลยอดซื้อ (AP)**")
            ap_file = st.file_uploader("Upload AP CSV", type=['csv'], key='ap')
            
            if ap_file:
                try:
                    df = pd.read_csv(ap_file)
                    st.session_state.ap_data = DataPreprocessor.prepare_ap_data(df)
                    st.success(f"✅ โหลด AP: {len(st.session_state.ap_data)} records")
                    
                    with st.expander("ดูข้อมูล AP"):
                        st.dataframe(st.session_state.ap_data.head(10))
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            st.write("**ข้อมูลที่เรียกเก็บ (AR)**")
            ar_file = st.file_uploader("Upload AR CSV", type=['csv'], key='ar')
            
            if ar_file:
                try:
                    df = pd.read_csv(ar_file)
                    st.session_state.ar_data = DataPreprocessor.prepare_ar_data(df)
                    st.success(f"✅ โหลด AR: {len(st.session_state.ar_data)} records")
                    
                    with st.expander("ดูข้อมูล AR"):
                        st.dataframe(st.session_state.ar_data.head(10))
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("🧮 คำนวณ Allowances")
        
        if st.session_state.ap_data is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💵 คำนวณ Allowances", type="primary", use_container_width=True):
                    with st.spinner("กำลังคำนวณ..."):
                        recon = TTAReconciliationSystem()
                        recon.tta_data = st.session_state.tta_data
                        recon.ap_data = st.session_state.ap_data
                        
                        calculated = recon.calculate_allowances()
                        
                        if calculated is not None and len(calculated) > 0:
                            st.session_state.calculated_allowances = calculated
                            st.success(f"✅ คำนวณสำเร็จ: {len(calculated)} รายการ")
                            st.metric("ยอดรวมที่ควรเรียกเก็บ", f"{calculated['calculated_amount'].sum():,.2f} บาท")
                        else:
                            st.error("❌ ไม่พบข้อมูลที่ match กัน")
            
            with col2:
                if st.session_state.calculated_allowances is not None and st.session_state.ar_data is not None:
                    if st.button("🔍 เปรียบเทียบกับ AR", type="primary", use_container_width=True):
                        with st.spinner("กำลังเปรียบเทียบ..."):
                            recon = TTAReconciliationSystem()
                            recon.tta_data = st.session_state.tta_data
                            recon.calculated_allowances = st.session_state.calculated_allowances
                            recon.ar_data = st.session_state.ar_data
                            
                            reconciliation = recon.reconcile_with_ar()
                            summary = recon.generate_summary_report()
                            
                            st.session_state.reconciliation_result = reconciliation
                            st.session_state.summary_report = summary
                            
                            st.success("✅ เปรียบเทียบเสร็จสิ้น!")
        else:
            st.warning("⚠️ กรุณาอัพโหลดข้อมูล AP ก่อน")
    
    with tab3:
        st.subheader("📊 ผลลัพธ์")
        
        if st.session_state.summary_report is not None:
            st.write("**สรุปภาพรวม:**")
            st.dataframe(st.session_state.summary_report, use_container_width=True)
            
            st.markdown("---")
            
            if st.session_state.reconciliation_result is not None:
                st.write("**รายละเอียดแต่ละ Category:**")
                st.dataframe(st.session_state.reconciliation_result, use_container_width=True)
                
                # Export
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export Summary
                    summary_csv = st.session_state.summary_report.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Download Summary CSV",
                        data=summary_csv,
                        file_name=f"TTA_Summary_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Export Detail
                    detail_csv = st.session_state.reconciliation_result.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Download Detail CSV",
                        data=detail_csv,
                        file_name=f"TTA_Detail_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        else:
            st.info("💡 กรุณาคำนวณและเปรียบเทียบข้อมูลในแท็บ 'Calculate' ก่อน")

# ========================================
# Page 3: Query Data
# ========================================

elif page == "📊 Query Data":
    st.header("📊 Query ข้อมูล Vendor")
    
    if not st.session_state.tta_data:
        st.warning("⚠️ กรุณาวิเคราะห์เอกสาร TTA ก่อน")
        st.stop()
    
    # Filters
    st.subheader("🔍 เลือก Vendor")
    
    vendor_keys = list(st.session_state.tta_data.keys())
    selected_vendor = st.selectbox(
        "Vendor Key",
        vendor_keys,
        help="เลือก Vendor ที่ต้องการดูรายละเอียด"
    )
    
    if selected_vendor:
        data = st.session_state.tta_data[selected_vendor]
        
        # Header Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Vendor Code", data.get('vendor_code'))
        with col2:
            st.metric("Division", f"{data.get('Division_code')} - {data.get('Division_name', 'N/A')}")
        with col3:
            st.metric("Department", f"{data.get('Department_code')} - {data.get('Department_name', 'N/A')}")
        with col4:
            allowances = data.get('allowances', [])
            st.metric("Allowances", len(allowances))
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Allowances", "💰 Calculated", "🔍 Reconciliation"])
        
        with tab1:
            st.subheader("📋 Allowances จาก TTA")
            
            if allowances:
                df = pd.DataFrame(allowances)
                
                # Display formatted table
                display_cols = ['category_code', 'category_name', 'rate_percent', 'fix_amount', 'payment_terms', 'description']
                available_cols = [col for col in display_cols if col in df.columns]
                
                st.dataframe(
                    df[available_cols],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Allowances CSV",
                    data=csv,
                    file_name=f"{selected_vendor}_allowances.csv",
                    mime="text/csv"
                )
            else:
                st.info("ไม่มีข้อมูล allowances")
        
        with tab2:
            st.subheader("💰 Calculated Allowances")
            
            if st.session_state.calculated_allowances is not None:
                vendor_calc = st.session_state.calculated_allowances[
                    st.session_state.calculated_allowances['tta_key'] == selected_vendor
                ]
                
                if not vendor_calc.empty:
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("ยอดซื้อ", f"{vendor_calc['purchase_amount'].iloc[0]:,.2f} บาท")
                    with col2:
                        st.metric("ยอดรวม Allowance", f"{vendor_calc['calculated_amount'].sum():,.2f} บาท")
                    with col3:
                        total_rate = vendor_calc[vendor_calc['rate_percent'].notna()]['rate_percent'].sum()
                        st.metric("รวม Rate", f"{total_rate:.2f}%")
                    
                    st.markdown("---")
                    
                    # Detail table
                    display_cols = ['category_code', 'category_name', 'calculation_type', 'calculated_amount']
                    st.dataframe(vendor_calc[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("ไม่มีข้อมูลการคำนวณสำหรับ vendor นี้")
            else:
                st.info("💡 กรุณาคำนวณ Allowances ในหน้า 'Calculate & Reconcile' ก่อน")
        
        with tab3:
            st.subheader("🔍 Reconciliation Result")
            
            if st.session_state.reconciliation_result is not None:
                vendor_recon = st.session_state.reconciliation_result[
                    st.session_state.reconciliation_result['tta_key'] == selected_vendor
                ]
                
                if not vendor_recon.empty:
                    # Summary
                    total_should = vendor_recon['should_collect'].sum()
                    total_actual = vendor_recon['actually_collected'].sum()
                    total_diff = vendor_recon['difference'].sum()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("ควรเรียกเก็บ", f"{total_should:,.2f} บาท")
                    with col2:
                        st.metric("เรียกเก็บจริง", f"{total_actual:,.2f} บาท")
                    with col3:
                        st.metric("ส่วนต่าง", f"{total_diff:,.2f} บาท", delta=f"{total_diff:,.2f}")
                    with col4:
                        if abs(total_diff) < 1:
                            st.success("✅ ครบ")
                        elif total_diff > 0:
                            st.warning("⚠️ เกิน")
                        else:
                            st.error("❌ ขาด")
                    
                    st.markdown("---")
                    
                    # Detail table with color coding
                    st.dataframe(
                        vendor_recon[['category_code', 'category_name', 'should_collect', 'actually_collected', 'difference', 'status']],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("ไม่มีข้อมูล reconciliation สำหรับ vendor นี้")
            else:
                st.info("💡 กรุณาทำ Reconciliation ในหน้า 'Calculate & Reconcile' ก่อน")
        
        # Raw JSON view
        st.markdown("---")
        with st.expander("🔍 View Raw JSON Data"):
            st.json(data)

# ========================================
# Footer
# ========================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>TTA Analysis System v1.0 | Powered by Google Gemini AI 🤖</p>
        <p><small>Built with Streamlit 🎈</small></p>
    </div>
    """,
    unsafe_allow_html=True
)
