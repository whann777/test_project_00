import streamlit as st
import os
import pandas as pd
from tta_core import TTADocumentAnalyzer, TTAReconciliationSystem, ALLOWANCE_CATEGORIES
import json
from datetime import datetime

def show():
    st.markdown("# 🔍 For Analyze")
    st.markdown("### วิเคราะห์และคำนวณ Agreement Contract")
    
    # Back button
    if st.button("← กลับหน้าหลัก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📄 วิเคราะห์เอกสาร", "🧮 คำนวณ & เปรียบเทียบ", "📊 ผลลัพธ์"])
    
    # ================== TAB 1: วิเคราะห์เอกสาร ==================
    with tab1:
        st.markdown("### 📄 อัปโหลดและวิเคราะห์เอกสาร PDF")
        
        # API Key input
        api_key = st.text_input(
            "🔑 Google Gemini API Key",
            type="password",
            help="ใส่ API Key จาก Google AI Studio"
        )
        
        if not api_key:
            st.warning("⚠️ กรุณาใส่ API Key เพื่อเริ่มการวิเคราะห์")
            st.info("""
            **วิธีการได้ API Key:**
            1. ไปที่ https://aistudio.google.com/app/apikey
            2. สร้าง API Key ใหม่
            3. Copy มาใส่ในช่องด้านบน
            """)
            return
        
        # File uploader
        uploaded_files = st.file_uploader(
            "อัปโหลดไฟล์ PDF (สามารถอัปโหลดหลายไฟล์)",
            type=['pdf'],
            accept_multiple_files=True,
            help="เลือกไฟล์ Agreement Contract ที่ต้องการวิเคราะห์"
        )
        
        if uploaded_files:
            st.success(f"✅ อัปโหลดสำเร็จ: {len(uploaded_files)} ไฟล์")
            
            # แสดงรายชื่อไฟล์
            with st.expander("📋 รายชื่อไฟล์ที่อัปโหลด"):
                for idx, file in enumerate(uploaded_files, 1):
                    st.write(f"{idx}. {file.name} ({file.size / 1024:.2f} KB)")
            
            # ปุ่มเริ่มวิเคราะห์
            if st.button("🚀 เริ่มวิเคราะห์", type="primary", use_container_width=True):
                analyze_documents(api_key, uploaded_files)
    
    # ================== TAB 2: คำนวณ & เปรียบเทียบ ==================
    with tab2:
        st.markdown("### 🧮 คำนวณและเปรียบเทียบข้อมูล")
        
        # เช็คว่ามีผล analysis หรือยัง
        if 'analysis_results' not in st.session_state or not st.session_state.analysis_results:
            st.warning("⚠️ กรุณาวิเคราะห์เอกสารใน Tab แรกก่อน")
            return
        
        st.success(f"✅ มีข้อมูลการวิเคราะห์: {len(st.session_state.analysis_results)} ไฟล์")
        
        # อัปโหลด AP และ AR files
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📥 ไฟล์ยอดซื้อ (AP)")
            ap_file = st.file_uploader(
                "Account Payable CSV",
                type=['csv'],
                key='ap_file',
                help="ไฟล์ข้อมูลยอดซื้อจาก Supplier"
            )
        
        with col2:
            st.markdown("#### 📥 ไฟล์ยอดเรียกเก็บ (AR)")
            ar_file = st.file_uploader(
                "Account Receivable CSV",
                type=['csv'],
                key='ar_file',
                help="ไฟล์ข้อมูลยอดที่เรียกเก็บจริง"
            )
        
        # ปุ่มคำนวณ
        if ap_file:
            st.info("💡 คุณสามารถคำนวณได้แม้ไม่มีไฟล์ AR (จะแสดงเฉพาะยอดที่ควรเรียกเก็บ)")
            
            if st.button("🧮 คำนวณและเปรียบเทียบ", type="primary", use_container_width=True):
                calculate_and_reconcile(ap_file, ar_file)
        else:
            st.warning("⚠️ กรุณาอัปโหลดไฟล์ AP เพื่อเริ่มคำนวณ")
    
    # ================== TAB 3: ผลลัพธ์ ==================
    with tab3:
        st.markdown("### 📊 ผลลัพธ์และรายงาน")
        
        if 'reconciliation_system' not in st.session_state:
            st.info("💡 กรุณาทำการคำนวณใน Tab ที่ 2 ก่อน")
            return
        
        recon = st.session_state.reconciliation_system
        
        # แสดงผลลัพธ์
        if recon.calculated_allowances is not None:
            display_results(recon)
        else:
            st.warning("⚠️ ไม่พบข้อมูลการคำนวณ")


def analyze_documents(api_key: str, uploaded_files):
    """วิเคราะห์เอกสาร PDF"""
    analyzer = TTADocumentAnalyzer(api_key)
    
    # สร้างโฟลเดอร์ temp
    temp_dir = "/tmp/tta_docs"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    analysis_results = []
    
    for idx, uploaded_file in enumerate(uploaded_files):
        # Save file
        pdf_path = os.path.join(temp_dir, uploaded_file.name)
        with open(pdf_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Update progress
        progress = (idx + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"กำลังวิเคราะห์ไฟล์ {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
        
        # Analyze
        with results_container:
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                result = analyzer.analyze_document(pdf_path)
                
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
                    
                    # แสดงรายละเอียด allowances
                    if result.get('allowances'):
                        st.markdown("**Allowances:**")
                        df_allowances = pd.DataFrame(result['allowances'])
                        st.dataframe(df_allowances, use_container_width=True)
                    
                    # บันทึกเป็น JSON
                    json_filename = uploaded_file.name.replace('.pdf', '_summary.json')
                    json_path = os.path.join(temp_dir, json_filename)
                    analyzer.save_summary(result, json_path)
                    
                    analysis_results.append({
                        'filename': uploaded_file.name,
                        'result': result,
                        'json_path': json_path
                    })
                else:
                    st.error("❌ การวิเคราะห์ล้มเหลว")
    
    progress_bar.progress(1.0)
    status_text.text("✅ วิเคราะห์เสร็จสิ้นทั้งหมด")
    
    # เก็บผลลัพธ์ใน session state
    st.session_state.analysis_results = analysis_results
    st.session_state.temp_dir = temp_dir
    
    # ปุ่ม Download JSON
    if analysis_results:
        st.markdown("---")
        st.markdown("### 💾 ดาวน์โหลดไฟล์ JSON")
        
        cols = st.columns(len(analysis_results))
        for idx, result_info in enumerate(analysis_results):
            with cols[idx]:
                with open(result_info['json_path'], 'r', encoding='utf-8') as f:
                    json_data = f.read()
                
                st.download_button(
                    label=f"📥 {result_info['filename'].replace('.pdf', '.json')}",
                    data=json_data,
                    file_name=result_info['filename'].replace('.pdf', '_summary.json'),
                    mime='application/json',
                    use_container_width=True
                )


def calculate_and_reconcile(ap_file, ar_file=None):
    """คำนวณและเปรียบเทียบข้อมูล"""
    
    # สร้าง system
    temp_dir = st.session_state.get('temp_dir', '/tmp/tta_docs')
    recon = TTAReconciliationSystem(base_folder=temp_dir)
    
    progress_text = st.empty()
    
    # บันทึกไฟล์ AP
    progress_text.text("📥 กำลังโหลดข้อมูล AP...")
    ap_path = os.path.join(temp_dir, ap_file.name)
    with open(ap_path, 'wb') as f:
        f.write(ap_file.getvalue())
    
    # บันทึกไฟล์ AR (ถ้ามี)
    if ar_file:
        progress_text.text("📥 กำลังโหลดข้อมูล AR...")
        ar_path = os.path.join(temp_dir, ar_file.name)
        with open(ar_path, 'wb') as f:
            f.write(ar_file.getvalue())
    
    # โหลดข้อมูล
    with st.spinner("กำลังประมวลผล..."):
        # Load TTA
        progress_text.text("📄 กำลังโหลดข้อมูล TTA...")
        json_files = [r['json_path'] for r in st.session_state.analysis_results]
        tta_loaded = recon.load_tta_summaries(json_files)
        
        # Load AP
        progress_text.text("📊 กำลังโหลดข้อมูล AP...")
        ap_loaded = recon.load_ap_data(ap_path)
        
        # Load AR
        ar_loaded = False
        if ar_file:
            progress_text.text("📊 กำลังโหลดข้อมูล AR...")
            ar_loaded = recon.load_ar_data(ar_path)
        
        # คำนวณ
        if tta_loaded and ap_loaded:
            progress_text.text("🧮 กำลังคำนวณ Allowances...")
            calculated = recon.calculate_allowances()
            
            # เปรียบเทียบกับ AR
            if ar_loaded:
                progress_text.text("🔍 กำลังเปรียบเทียบกับ AR...")
                reconciliation = recon.reconcile_with_ar()
    
    progress_text.text("✅ ดำเนินการเสร็จสมบูรณ์!")
    
    # เก็บ system ใน session state
    st.session_state.reconciliation_system = recon
    
    st.success("✅ คำนวณและเปรียบเทียบสำเร็จ! ไปที่ Tab 'ผลลัพธ์' เพื่อดูรายงาน")
    st.balloons()


def display_results(recon: TTAReconciliationSystem):
    """แสดงผลลัพธ์"""
    
    # Summary metrics
    st.markdown("### 📈 สรุปภาพรวม")
    
    if recon.reconciliation_result is not None:
        summary = recon.generate_summary_report()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "จำนวน Vendor",
                len(summary)
            )
        
        with col2:
            st.metric(
                "ควรเรียกเก็บทั้งหมด",
                f"฿{summary['should_collect'].sum():,.2f}"
            )
        
        with col3:
            st.metric(
                "เรียกเก็บจริงทั้งหมด",
                f"฿{summary['actually_collected'].sum():,.2f}"
            )
        
        with col4:
            diff = summary['difference'].sum()
            st.metric(
                "ส่วนต่าง",
                f"฿{diff:,.2f}",
                delta=f"{diff:,.2f}",
                delta_color="inverse" if diff < 0 else "normal"
            )
        
        st.markdown("---")
        
        # Summary table
        st.markdown("### 📊 รายงานสรุปตาม Vendor")
        st.dataframe(
            summary.style.format({
                'should_collect': '฿{:,.2f}',
                'actually_collected': '฿{:,.2f}',
                'difference': '฿{:,.2f}',
                'variance_pct': '{:.2f}%'
            }),
            use_container_width=True
        )
        
        # Detailed view
        st.markdown("---")
        st.markdown("### 🔍 รายละเอียดแต่ละหมวดหมู่")
        
        # เลือก Vendor
        vendors = recon.reconciliation_result['vendor_code'].unique()
        selected_vendor = st.selectbox(
            "เลือก Vendor",
            options=['ทั้งหมด'] + list(vendors)
        )
        
        # Filter data
        if selected_vendor == 'ทั้งหมด':
            filtered_data = recon.reconciliation_result
        else:
            filtered_data = recon.reconciliation_result[
                recon.reconciliation_result['vendor_code'] == selected_vendor
            ]
        
        st.dataframe(
            filtered_data.style.format({
                'should_collect': '฿{:,.2f}',
                'actually_collected': '฿{:,.2f}',
                'difference': '฿{:,.2f}',
                'variance_pct': '{:.2f}%'
            }),
            use_container_width=True
        )
    
    else:
        # แสดงเฉพาะ calculated allowances
        st.markdown("### 💰 ยอดที่ควรเรียกเก็บ")
        st.info("ℹ️ ไม่มีข้อมูล AR - แสดงเฉพาะยอดที่คำนวณได้")
        
        st.dataframe(
            recon.calculated_allowances.style.format({
                'total_purchase': '฿{:,.2f}',
                'should_collect': '฿{:,.2f}',
                'rate_percent': '{:.2f}%',
                'fix_amount': '฿{:,.2f}'
            }),
            use_container_width=True
        )
    
    # Export buttons
    st.markdown("---")
    st.markdown("### 💾 Export รายงาน")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export เป็น Excel", type="primary", use_container_width=True):
            output_file = recon.export_results()
            if output_file:
                with open(output_file, 'rb') as f:
                    st.download_button(
                        label="📥 ดาวน์โหลด Excel",
                        data=f,
                        file_name=os.path.basename(output_file),
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        use_container_width=True
                    )
    
    with col2:
        if recon.reconciliation_result is not None:
            csv_data = recon.reconciliation_result.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Export เป็น CSV",
                data=csv_data,
                file_name=f"TTA_Reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                use_container_width=True
            )
