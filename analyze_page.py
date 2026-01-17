import streamlit as st
import os
import pandas as pd
from pathlib import Path
import config
from tta_core import TTADocumentAnalyzer, TTAReconciliationSystem
import json
from datetime import datetime
import time

def show():
    st.markdown("""
        <style>
        .process-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .process-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #2D3748;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        .success-box {
            background: #d4edda;
            border-left: 4px solid #28a745;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-box {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .info-box {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("# 🔍 Analysis Mode")
        st.markdown("### วิเคราะห์และคำนวณอัตโนมัติ")
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
    
    st.markdown("---")
    
    # ตรวจสอบไฟล์ในโฟลเดอร์
    check_and_display_files()
    
    st.markdown("---")
    
    # ปุ่มเริ่มประมวลผล
    if st.button("🚀 เริ่มประมวลผลทั้งหมด", type="primary", use_container_width=True):
        process_all_files()
    
    # แสดงผลลัพธ์ถ้ามี
    if 'processing_done' in st.session_state and st.session_state.processing_done:
        st.markdown("---")
        display_results()


def check_and_display_files():
    """ตรวจสอบและแสดงไฟล์ในโฟลเดอร์"""
    
    st.markdown('<div class="process-card">', unsafe_allow_html=True)
    st.markdown('<div class="process-title">📁 ไฟล์ที่พร้อมประมวลผล</div>', unsafe_allow_html=True)
    
    # นับจำนวนไฟล์
    pdf_files = list(Path(config.PDF_FOLDER).glob("*.pdf"))
    ap_files = list(Path(config.AP_FOLDER).glob("*.csv"))
    ar_files = list(Path(config.AR_FOLDER).glob("*.csv"))
    
    # แสดง metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(pdf_files)}</div>
            <div class="metric-label">📄 Agreement PDF</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(ap_files)}</div>
            <div class="metric-label">📊 AP Files</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(ar_files)}</div>
            <div class="metric-label">💰 AR Files</div>
        </div>
        """, unsafe_allow_html=True)
    
    # แสดงรายชื่อไฟล์
    if len(pdf_files) > 0 or len(ap_files) > 0 or len(ar_files) > 0:
        with st.expander("📋 รายชื่อไฟล์ทั้งหมด", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**PDF Files:**")
                if pdf_files:
                    for f in pdf_files:
                        st.text(f"✓ {f.name}")
                else:
                    st.text("ไม่พบไฟล์")
            
            with col2:
                st.markdown("**AP Files:**")
                if ap_files:
                    for f in ap_files:
                        st.text(f"✓ {f.name}")
                else:
                    st.text("ไม่พบไฟล์")
            
            with col3:
                st.markdown("**AR Files:**")
                if ar_files:
                    for f in ar_files:
                        st.text(f"✓ {f.name}")
                else:
                    st.text("ไม่พบไฟล์")
    
    # คำเตือนถ้าไม่มีไฟล์
    if len(pdf_files) == 0:
        st.markdown(f"""
        <div class="error-box">
            <b>⚠️ ไม่พบไฟล์ PDF</b><br>
            กรุณาวางไฟล์ Agreement PDF ในโฟลเดอร์: <code>{config.PDF_FOLDER}</code>
        </div>
        """, unsafe_allow_html=True)
    
    if len(ap_files) == 0:
        st.markdown(f"""
        <div class="error-box">
            <b>⚠️ ไม่พบไฟล์ AP</b><br>
            กรุณาวางไฟล์ AP CSV ในโฟลเดอร์: <code>{config.AP_FOLDER}</code>
        </div>
        """, unsafe_allow_html=True)
    
    if len(ar_files) == 0:
        st.markdown(f"""
        <div class="info-box">
            <b>ℹ️ ไม่พบไฟล์ AR</b><br>
            ระบบจะคำนวณเฉพาะยอดที่ควรเรียกเก็บ (ไม่มีการเปรียบเทียบ)<br>
            หากต้องการเปรียบเทียบ กรุณาวางไฟล์ AR CSV ในโฟลเดอร์: <code>{config.AR_FOLDER}</code>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def process_all_files():
    """ประมวลผลไฟล์ทั้งหมดอัตโนมัติ"""
    
    # ตรวจสอบไฟล์
    pdf_files = list(Path(config.PDF_FOLDER).glob("*.pdf"))
    ap_files = list(Path(config.AP_FOLDER).glob("*.csv"))
    ar_files = list(Path(config.AR_FOLDER).glob("*.csv"))
    
    if len(pdf_files) == 0 or len(ap_files) == 0:
        st.error("❌ ไม่สามารถเริ่มประมวลผลได้ เนื่องจากไม่มีไฟล์ PDF หรือ AP")
        return
    
    # สร้าง progress container
    progress_container = st.container()
    
    with progress_container:
        st.markdown('<div class="process-card">', unsafe_allow_html=True)
        st.markdown('<div class="process-title">⚙️ กำลังประมวลผล...</div>', unsafe_allow_html=True)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: วิเคราะห์ PDF
        status_text.markdown("### 📄 Step 1: วิเคราะห์เอกสาร PDF")
        analyzer = TTADocumentAnalyzer(config.GEMINI_API_KEY)
        
        analysis_results = []
        json_files = []
        
        for idx, pdf_file in enumerate(pdf_files):
            progress = (idx + 1) / (len(pdf_files) + 2)  # +2 สำหรับ AP/AR processing
            progress_bar.progress(progress)
            
            with st.expander(f"📄 {pdf_file.name}", expanded=True):
                st.info(f"กำลังวิเคราะห์... ({idx + 1}/{len(pdf_files)})")
                
                result = analyzer.analyze_document(str(pdf_file))
                
                if result:
                    st.success("✅ วิเคราะห์สำเร็จ")
                    
                    # แสดงข้อมูลสรุป
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Vendor Code", result.get('vendor_code', 'N/A'))
                    with col2:
                        st.metric("Division", result.get('Division_name', 'N/A'))
                    with col3:
                        st.metric("Allowances", len(result.get('allowances', [])))
                    
                    # บันทึก JSON
                    json_filename = pdf_file.stem + '_summary.json'
                    json_path = Path(config.TEMP_FOLDER) / json_filename
                    analyzer.save_summary(result, str(json_path))
                    
                    analysis_results.append(result)
                    json_files.append(str(json_path))
                else:
                    st.error("❌ การวิเคราะห์ล้มเหลว")
        
        # Step 2: คำนวณและเปรียบเทียบ
        if analysis_results:
            progress_bar.progress(0.7)
            status_text.markdown("### 🧮 Step 2: คำนวณและเปรียบเทียบข้อมูล")
            
            # สร้าง reconciliation system
            recon = TTAReconciliationSystem(base_folder=config.TEMP_FOLDER)
            
            # โหลด TTA
            st.info("📊 กำลังโหลดข้อมูล TTA...")
            st.write(f"Debug: พบ {len(json_files)} ไฟล์ JSON")
            for jf in json_files:
                st.write(f"- {jf}")
            
            tta_loaded = recon.load_tta_summaries(json_files)
            
            if tta_loaded:
                # โหลด AP
                st.info("📊 กำลังโหลดข้อมูล AP...")
                ap_file = str(ap_files[0])  # ใช้ไฟล์แรก
                ap_loaded = recon.load_ap_data(ap_file)
                
                if ap_loaded:
                    # คำนวณ
                    progress_bar.progress(0.8)
                    st.info("🧮 กำลังคำนวณ Allowances...")
                    calculated = recon.calculate_allowances()
                    
                    if calculated is not None:
                        st.success(f"✅ คำนวณสำเร็จ: {len(calculated)} รายการ")
                        
                        # เปรียบเทียบกับ AR (ถ้ามี)
                        if len(ar_files) > 0:
                            progress_bar.progress(0.9)
                            st.info("🔍 กำลังเปรียบเทียบกับ AR...")
                            ar_file = str(ar_files[0])  # ใช้ไฟล์แรก
                            ar_loaded = recon.load_ar_data(ar_file)
                            
                            if ar_loaded:
                                reconciliation = recon.reconcile_with_ar()
                                if reconciliation is not None:
                                    st.success(f"✅ เปรียบเทียบสำเร็จ: {len(reconciliation)} รายการ")
                        
                        # Export ผลลัพธ์
                        progress_bar.progress(0.95)
                        st.info("💾 กำลัง Export รายงาน...")
                        output_file = recon.export_results(output_folder=config.OUTPUT_FOLDER)
                        
                        if output_file:
                            st.success(f"✅ Export สำเร็จ: {os.path.basename(output_file)}")
                            
                            # เก็บข้อมูลใน session state
                            st.session_state.reconciliation_system = recon
                            st.session_state.processing_done = True
                            st.session_state.output_file = output_file
                            
                            progress_bar.progress(1.0)
                            status_text.markdown("### ✅ ประมวลผลเสร็จสมบูรณ์!")
                            st.balloons()
                        else:
                            st.error("❌ Export ล้มเหลว")
                    else:
                        st.error("❌ การคำนวณล้มเหลว")
                else:
                    st.error("❌ โหลดข้อมูล AP ล้มเหลว")
            else:
                st.error("❌ โหลดข้อมูล TTA ล้มเหลว")
                st.write(f"Debug: json_files = {json_files}")
                st.write(f"Debug: TEMP_FOLDER = {config.TEMP_FOLDER}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_results():
    """แสดงผลลัพธ์การประมวลผล"""
    
    if 'reconciliation_system' not in st.session_state:
        return
    
    recon = st.session_state.reconciliation_system
    
    st.markdown('<div class="process-card">', unsafe_allow_html=True)
    st.markdown('<div class="process-title">📊 ผลลัพธ์การประมวลผล</div>', unsafe_allow_html=True)
    
    # Summary metrics
    if recon.reconciliation_result is not None:
        summary = recon.generate_summary_report()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "จำนวน Vendor",
                len(summary),
                help="จำนวน Vendor ทั้งหมด"
            )
        
        with col2:
            total_should = summary['should_collect'].sum()
            st.metric(
                "ควรเรียกเก็บทั้งหมด",
                f"฿{total_should:,.0f}",
                help="ยอดรวมที่ควรเรียกเก็บ"
            )
        
        with col3:
            total_actual = summary['actually_collected'].sum()
            st.metric(
                "เรียกเก็บจริงทั้งหมด",
                f"฿{total_actual:,.0f}",
                help="ยอดรวมที่เรียกเก็บจริง"
            )
        
        with col4:
            diff = summary['difference'].sum()
            st.metric(
                "ส่วนต่างรวม",
                f"฿{diff:,.0f}",
                delta=f"{diff:,.0f}",
                delta_color="inverse" if diff < 0 else "normal",
                help="ผลต่างระหว่างที่เรียกเก็บจริงกับที่ควรเรียกเก็บ"
            )
        
        st.markdown("---")
        
        # แสดงตารางสรุป
        st.markdown("### 📋 รายงานสรุปตาม Vendor")
        st.dataframe(
            summary.style.format({
                'should_collect': '฿{:,.2f}',
                'actually_collected': '฿{:,.2f}',
                'difference': '฿{:,.2f}',
                'variance_pct': '{:.2f}%'
            }),
            use_container_width=True,
            height=400
        )
    
    else:
        # แสดงเฉพาะ calculated
        if recon.calculated_allowances is not None:
            st.info("ℹ️ ไม่มีข้อมูล AR - แสดงเฉพาะยอดที่คำนวณได้")
            
            st.markdown("### 💰 ยอดที่ควรเรียกเก็บ")
            st.dataframe(
                recon.calculated_allowances.style.format({
                    'total_purchase': '฿{:,.2f}',
                    'should_collect': '฿{:,.2f}',
                    'rate_percent': '{:.2f}%',
                    'fix_amount': '฿{:,.2f}'
                }),
                use_container_width=True,
                height=400
            )
    
    # Download button
    st.markdown("---")
    st.markdown("### 💾 ดาวน์โหลดรายงาน")
    
    if 'output_file' in st.session_state and os.path.exists(st.session_state.output_file):
        with open(st.session_state.output_file, 'rb') as f:
            st.download_button(
                label="📥 ดาวน์โหลด Excel Report",
                data=f,
                file_name=os.path.basename(st.session_state.output_file),
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary",
                use_container_width=True
            )
    
    # ปุ่มไป Dashboard
    st.markdown("---")
    if st.button("📊 ดูผลใน Dashboard", type="primary", use_container_width=True):
        # โหลดข้อมูลเข้า auditor mode
        if 'output_file' in st.session_state:
            try:
                calculated_df = pd.read_excel(st.session_state.output_file, sheet_name='Calculated')
                reconciliation_df = pd.read_excel(st.session_state.output_file, sheet_name='Reconciliation')
                summary_df = pd.read_excel(st.session_state.output_file, sheet_name='Summary')
                
                st.session_state.auditor_data = {
                    'calculated': calculated_df,
                    'reconciliation': reconciliation_df,
                    'summary': summary_df,
                    'upload_time': datetime.now()
                }
                
                st.session_state.mode = "auditor"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error loading data: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
