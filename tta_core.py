import google.generativeai as genai
from pdf2image import convert_from_path
import json
import time
import os
from typing import Dict, List
import pandas as pd
from datetime import datetime

# กำหนด categories ของ allowance
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
    "SPD": "Special Discount",
    "CCS": "Clearance/Markdown"
}


class TTADocumentAnalyzer:
    def __init__(self, api_key: str):
        """Initialize Gemini API"""
        genai.configure(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(self.model_name)

    def create_analysis_prompt(self) -> str:
        categories_text = "\n".join([f"- {code}: {name}" for code, name in ALLOWANCE_CATEGORIES.items()])
        
        prompt = f"""
        คุณคือผู้เชี่ยวชาญด้านสัญญาการค้า (Trade Terms)
        โปรดวิเคราะห์ไฟล์เอกสารแนบนี้ (PDF) ซึ่งเป็นข้อตกลงทางการค้า และดึงข้อมูลออกมาในรูปแบบ JSON:

        1. หา Vendor Code, Division Code, Division Name, Department Code, Division Name จากเอกสาร
          **เอกสารทุกไฟล์จะมี Vendor Code, Division Code, Division Name, Department Code, Division Name เสมอ บางเอกสารอาจมีมากกว่า 1 Department **
          - Division Code จะขึ้นต้นด้วย 0 เสมอ เช่น 01, 02, 03
          - บางไฟล์ Department สามารถมีได้มากกว่า 1 ดังนั้นช่วยหยิบมาให้ครบ

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
        1. **Header vs Detail:** ข้อมูลส่วนหัว Total Contract (เช่น % Auto Rate, Fix Amount) จะเป็น "ผลรวม" ของรายการย่อย ให้โฟกัสที่การดึง "รายการย่อย" (Line Items) ให้ครบทุกบรรทัด
        2. **เมื่อดึงรายการย่อยที่มี Rate หรือ Fix Amount ออกมาครบทุกหัวข้อใน Page 1 แล้ว สามารถตรวจความถูกต้องได้จากผลรวมของ Rate และ Fix Amount ที่ดึงออกมาได้จะต้องได้เท่ากับ % Auto Rate และ Fix Amount ตาม Header
        3. **Page 2 Analysis:** หน้า 2 มักเป็นเงื่อนไขเพิ่มเติม (Additional Conditions) ที่ไม่มีรหัสกำกับ ต้องอ่านบริบทแล้ว map เข้า Category ที่ถูกต้อง
           - ถ้าเจอคำว่า "Leaflet", "Brochure", "Ad" -> ให้ map เป็น "BRO"
        4. **Calculation:** หากเจอเงื่อนไขแบบ "per time" หรือ "per month" ให้คำนวณเป็น "ยอดรวมต่อปี" (Annual Total) ในช่อง fix_amount เสมอ พร้อมใส่เงื่อนไขในการคำนวณมาให้ด้วย

        **สำคัญ**:
        - หน้า 1 สนใจเฉพาะส่วนที่มีหัวข้อชัดเจนเท่านั้น ไม่ต้องสนใจเนื้อหาในส่วน Others Agreement
        - ถ้า CRB มีการให้ rate หรือ Fix Amount หัวข้อ ARB จะต้องมี rate หรือ Fix Amount เสมอ
        - หน้า 2 อาจจะมีทั้งส่วนที่มีหัวข้อชัดเจนและไม่ชัดเจน ให้วิเคราะห์หน้า 2 อย่างละเอียดโดยวิเคราะห์จากบริบทและเนื้อหา
        - ถ้าหน้า 2 ไม่มีหัวข้อชัดเจน ให้วิเคราะห์จากเนื้อหาและจัดกลุ่มให้ตรงกับหมวดหมู่ที่กำหนดไว้
        - ถ้ามีทั้ง Rate และ Fix Amount ให้ระบุทั้งสอง
        - อ่านข้อมูลจากตารางในเอกสารให้ละเอียดระวังเรื่องบรรทัดและคอลัมน์
        - ไม่ต้องสนใจส่วนที่เป็นลายมือหรือสิ่งที่เป็นคนเขียน
        - สรุปเฉพาะหัวข้อที่มี Rate หรือ Fix Amount

        Response ในรูปแบบ JSON เท่านั้น:
      {{
        "vendor_code": "รหัสผู้ขาย",
        "Division_code": "รหัสแผนก",
        "Division_name": "ชื่อแผนก",
        "Department_code": "รหัสฝ่าย",
        "Department_name": "ชื่อฝ่าย",
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
    """วิเคราะห์เอกสาร PDF"""
        try:
            print(f"\n🤖 กำลังวิเคราะห์: {os.path.basename(pdf_path)}")
            
            # Upload file
            doc_file = genai.upload_file(path=pdf_path, display_name="Trade_Term_Doc")
            
            # รอ Processing
            print("   รอการประมวลผล", end='')
            while doc_file.state.name == "PROCESSING":
                print('.', end='')
                time.sleep(2)
                doc_file = genai.get_file(doc_file.name)
            print(" ✓")
            
            if doc_file.state.name == "FAILED":
                raise ValueError(f"การประมวลผลล้มเหลว: {doc_file.state.name}")
            
            # Generate content
            print("   กำลังวิเคราะห์เอกสาร...")
            prompt = self.create_analysis_prompt()
            response = self.model.generate_content([doc_file, prompt])
            
            # Parse JSON
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            
            # Clean up
            genai.delete_file(doc_file.name)
            
            print("   ✅ วิเคราะห์สำเร็จ")
            return result
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")  # เพิ่มบรรทัดนี้
            print(f"   ❌ Error type: {type(e).__name__}")  # เพิ่มบรรทัดนี้
            import traceback
            print(f"   ❌ Traceback: {traceback.format_exc()}")  # เพิ่มบรรทัดนี้
            return None
        
    def save_summary(self, analysis_result: Dict, output_path: str):
        """บันทึกผลการวิเคราะห์เป็น JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False


class TTAReconciliationSystem:
    def __init__(self, base_folder: str = "."):
        self.base_folder = base_folder
        self.tta_data = None
        self.ap_data = None
        self.ar_data = None
        self.calculated_allowances = None
        self.reconciliation_result = None

    def load_tta_summaries(self, json_files: List[str] = None) -> bool:
        """โหลดไฟล์ JSON ที่มีผลการวิเคราะห์"""
        try:
            if json_files is None:
                json_files = [f for f in os.listdir(self.base_folder) if f.endswith('_summary.json')]
            
            if not json_files:
                print("❌ ไม่พบไฟล์ JSON")
                return False
            
            all_data = []
            for json_file in json_files:
                filepath = os.path.join(self.base_folder, json_file) if not os.path.isabs(json_file) else json_file
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.append(data)
            
            self.tta_data = all_data
            print(f"✅ โหลด TTA สำเร็จ: {len(all_data)} ไฟล์")
            return True
            
        except Exception as e:
            print(f"❌ Error loading TTA: {e}")
            return False

    def load_ap_data(self, csv_file: str = None) -> bool:
        """โหลดข้อมูล Account Payable (ยอดซื้อ)"""
        try:
            if csv_file is None:
                csv_files = [f for f in os.listdir(self.base_folder) if 'Account_Payable' in f and f.endswith('.csv')]
                if not csv_files:
                    print("❌ ไม่พบไฟล์ AP CSV")
                    return False
                csv_file = csv_files[0]
            
            filepath = os.path.join(self.base_folder, csv_file) if not os.path.isabs(csv_file) else csv_file
            self.ap_data = pd.read_csv(filepath)
            
            # สร้าง match key
            self.ap_data['TTA_MATCH_KEY'] = (
                self.ap_data['VENDOR_ID'].astype(str) + '_' +
                self.ap_data['DIVISION_ID'].astype(str).str.zfill(2) + '_' +
                self.ap_data['DEPARTMENT_ID'].astype(str).str.zfill(3)
            )
            
            print(f"✅ โหลด AP สำเร็จ: {len(self.ap_data):,} รายการ")
            return True
            
        except Exception as e:
            print(f"❌ Error loading AP: {e}")
            return False

    def load_ar_data(self, csv_file: str = None) -> bool:
        """โหลดข้อมูล Account Receivable (ยอดเรียกเก็บ)"""
        try:
            if csv_file is None:
                csv_files = [f for f in os.listdir(self.base_folder) if 'AR_Detail' in f and f.endswith('.csv')]
                if not csv_files:
                    print("❌ ไม่พบไฟล์ AR CSV")
                    return False
                csv_file = csv_files[0]
            
            filepath = os.path.join(self.base_folder, csv_file) if not os.path.isabs(csv_file) else csv_file
            self.ar_data = pd.read_csv(filepath)
            
            # Clean REF_TYPE
            self.ar_data['REF_TYPE_CLEAN'] = self.ar_data['REF_TYPE'].str.strip().str.upper()
            
            # สร้าง match key
            self.ar_data['TTA_MATCH_KEY'] = (
                self.ar_data['VENDOR_ID'].astype(str) + '_' +
                self.ar_data['DIVISION_ID'].astype(str).str.zfill(2) + '_' +
                self.ar_data['DEPARTMENT_ID'].astype(str).str.zfill(3)
            )
            
            print(f"✅ โหลด AR สำเร็จ: {len(self.ar_data):,} รายการ")
            return True
            
        except Exception as e:
            print(f"❌ Error loading AR: {e}")
            return False

    def calculate_allowances(self) -> pd.DataFrame:
        """คำนวณยอดที่ควรเรียกเก็บตาม TTA"""
        if self.tta_data is None or self.ap_data is None:
            print("❌ ต้องโหลด TTA และ AP ก่อน")
            return None
        
        results = []
        
        for tta_doc in self.tta_data:
            vendor_code = tta_doc.get('vendor_code', '')
            division_code = str(tta_doc.get('Division_code', '')).zfill(2)
            
            # รองรับหลาย Department
            dept_codes = tta_doc.get('Department_code', [])
            if not isinstance(dept_codes, list):
                dept_codes = [dept_codes]
            
            for dept_code in dept_codes:
                dept_code_str = str(dept_code).zfill(3)
                tta_key = f"{vendor_code}_{division_code}_{dept_code_str}"
                
                # Filter AP data
                ap_subset = self.ap_data[self.ap_data['TTA_MATCH_KEY'] == tta_key]
                
                if ap_subset.empty:
                    continue
                
                total_purchase = ap_subset['EXTENDED_AMOUNT'].sum()
                vendor_name = ap_subset['VENDOR_NAME'].iloc[0] if len(ap_subset) > 0 else ''
                
                # คำนวณแต่ละ allowance
                for allowance in tta_doc.get('allowances', []):
                    category_code = allowance.get('category_code', '')
                    category_name = allowance.get('category_name', '')
                    rate_percent = allowance.get('rate_percent')
                    fix_amount = allowance.get('fix_amount')
                    description = allowance.get('description', '')
                    payment_terms = allowance.get('payment_terms', '')
                    
                    # คำนวณยอดที่ควรเรียกเก็บ
                    should_collect = 0
                    if rate_percent:
                        should_collect = total_purchase * (rate_percent / 100)
                    if fix_amount:
                        should_collect += fix_amount
                    
                    results.append({
                        'tta_key': tta_key,
                        'vendor_code': vendor_code,
                        'vendor_name': vendor_name,
                        'division_code': division_code,
                        'department_code': dept_code_str,
                        'category_code': category_code,
                        'category_name': category_name,
                        'rate_percent': rate_percent,
                        'fix_amount': fix_amount,
                        'total_purchase': total_purchase,
                        'should_collect': should_collect,
                        'description': description,
                        'payment_terms': payment_terms
                    })
        
        self.calculated_allowances = pd.DataFrame(results)
        print(f"✅ คำนวณสำเร็จ: {len(results)} รายการ")
        return self.calculated_allowances

    def reconcile_with_ar(self) -> pd.DataFrame:
        """เปรียบเทียบกับยอดเรียกเก็บจริง"""
        if self.calculated_allowances is None or self.ar_data is None:
            print("❌ ต้องคำนวณ allowances และโหลด AR ก่อน")
            return None
        
        reconciliation_results = []
        
        for tta_key in self.calculated_allowances['tta_key'].unique():
            tta_subset = self.calculated_allowances[self.calculated_allowances['tta_key'] == tta_key]
            vendor_code = tta_subset['vendor_code'].iloc[0]
            vendor_name = tta_subset['vendor_name'].iloc[0]
            
            for _, row in tta_subset.iterrows():
                category_code = row['category_code']
                category_name = row['category_name']
                should_collect = row['should_collect']
                
                # หา AR ที่ match
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
        print(f"✅ เปรียบเทียบสำเร็จ: {len(reconciliation_results)} รายการ")
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

    def export_results(self, output_folder: str = None) -> str:
        """Export ผลลัพธ์เป็น Excel"""
        if output_folder is None:
            output_folder = self.base_folder
        
        try:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_folder, f"TTA_Reconciliation_{timestamp}.xlsx")
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if self.calculated_allowances is not None:
                    self.calculated_allowances.to_excel(writer, sheet_name='Calculated', index=False)
                
                if self.reconciliation_result is not None:
                    self.reconciliation_result.to_excel(writer, sheet_name='Reconciliation', index=False)
                
                summary = self.generate_summary_report()
                if summary is not None:
                    summary.to_excel(writer, sheet_name='Summary', index=False)
            
            print(f"✅ Export สำเร็จ: {os.path.basename(filename)}")
            return filename
        except Exception as e:
            print(f"❌ Error exporting: {e}")
            return None
