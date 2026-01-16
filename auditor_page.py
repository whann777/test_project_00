import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json

def show():
    st.markdown("# 📋 For Auditor")
    st.markdown("### Dashboard และตรวจสอบข้อมูล")
    
    # Back button
    if st.button("← กลับหน้าหลัก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Sidebar for file upload
    with st.sidebar:
        st.markdown("## 📁 อัปโหลดข้อมูล")
        st.markdown("อัปโหลดไฟล์ผลลัพธ์จากการวิเคราะห์")
        
        # อัปโหลด Excel file
        excel_file = st.file_uploader(
            "📊 ไฟล์ Excel Reconciliation",
            type=['xlsx'],
            help="ไฟล์ที่ export จาก For Analyze"
        )
        
        if excel_file:
            load_data(excel_file)
    
    # เช็คว่ามีข้อมูลหรือยัง
    if 'auditor_data' not in st.session_state:
        st.info("""
        ### 💡 วิธีใช้งาน
        1. อัปโหลดไฟล์ Excel ที่ได้จากการวิเคราะห์
        2. ระบบจะแสดง Dashboard และข้อมูลโดยละเอียด
        3. คุณสามารถกรอง ค้นหา และ Export ข้อมูลได้
        
        **หมายเหตุ:** กรุณาอัปโหลดไฟล์ Excel ที่ Sidebar ด้านซ้าย
        """)
        return
    
    # แสดง Dashboard
    display_dashboard()


def load_data(excel_file):
    """โหลดข้อมูลจาก Excel file"""
    try:
        # อ่าน sheets
        calculated_df = pd.read_excel(excel_file, sheet_name='Calculated')
        reconciliation_df = pd.read_excel(excel_file, sheet_name='Reconciliation')
        summary_df = pd.read_excel(excel_file, sheet_name='Summary')
        
        # เก็บใน session state
        st.session_state.auditor_data = {
            'calculated': calculated_df,
            'reconciliation': reconciliation_df,
            'summary': summary_df,
            'upload_time': datetime.now()
        }
        
        st.sidebar.success("✅ โหลดข้อมูลสำเร็จ!")
        
    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {e}")


def display_dashboard():
    """แสดง Dashboard"""
    
    data = st.session_state.auditor_data
    summary_df = data['summary']
    reconciliation_df = data['reconciliation']
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard ภาพรวม",
        "🔍 รายละเอียดตาม Vendor",
        "📈 การวิเคราะห์",
        "💾 Export ข้อมูล"
    ])
    
    # =============== TAB 1: Dashboard ภาพรวม ===============
    with tab1:
        display_overview_dashboard(summary_df, reconciliation_df)
    
    # =============== TAB 2: รายละเอียดตาม Vendor ===============
    with tab2:
        display_vendor_details(reconciliation_df)
    
    # =============== TAB 3: การวิเคราะห์ ===============
    with tab3:
        display_analysis(summary_df, reconciliation_df)
    
    # =============== TAB 4: Export ข้อมูล ===============
    with tab4:
        display_export_options(data)


def display_overview_dashboard(summary_df, reconciliation_df):
    """Dashboard ภาพรวม"""
    
    st.markdown("### 📊 สรุปภาพรวม")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "จำนวน Vendor ทั้งหมด",
            len(summary_df),
            help="จำนวน Vendor ที่มีข้อมูล"
        )
    
    with col2:
        total_should = summary_df['should_collect'].sum()
        st.metric(
            "ควรเรียกเก็บทั้งหมด",
            f"฿{total_should:,.0f}",
            help="ยอดรวมที่ควรเรียกเก็บจากทุก Vendor"
        )
    
    with col3:
        total_actual = summary_df['actually_collected'].sum()
        st.metric(
            "เรียกเก็บจริงทั้งหมด",
            f"฿{total_actual:,.0f}",
            help="ยอดรวมที่เรียกเก็บจริง"
        )
    
    with col4:
        total_diff = summary_df['difference'].sum()
        st.metric(
            "ส่วนต่างรวม",
            f"฿{total_diff:,.0f}",
            delta=f"{total_diff:,.0f}",
            delta_color="inverse" if total_diff < 0 else "normal",
            help="ผลต่างระหว่างที่เรียกเก็บจริงกับที่ควรเรียกเก็บ"
        )
    
    st.markdown("---")
    
    # Status breakdown
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 สถานะการเรียกเก็บ")
        status_counts = summary_df['status'].value_counts()
        
        # Pie chart
        fig_status = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,
            marker_colors=['#4CAF50', '#FFC107', '#F44336']
        )])
        fig_status.update_layout(
            showlegend=True,
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Top 5 Vendor (ตามยอดที่ควรเรียกเก็บ)")
        top_vendors = summary_df.nlargest(5, 'should_collect')[['vendor_name', 'should_collect', 'status']]
        
        fig_top = go.Figure(data=[
            go.Bar(
                x=top_vendors['should_collect'],
                y=top_vendors['vendor_name'],
                orientation='h',
                text=top_vendors['should_collect'].apply(lambda x: f'฿{x:,.0f}'),
                textposition='auto',
                marker_color='#2196F3'
            )
        ])
        fig_top.update_layout(
            showlegend=False,
            height=300,
            xaxis_title="ยอดที่ควรเรียกเก็บ (บาท)",
            yaxis_title="",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    st.markdown("---")
    
    # Summary table with search
    st.markdown("#### 📋 ตารางสรุป")
    
    # Search box
    search_term = st.text_input("🔍 ค้นหา Vendor", placeholder="พิมพ์รหัสหรือชื่อ Vendor")
    
    # Filter data
    if search_term:
        filtered_summary = summary_df[
            summary_df['vendor_code'].astype(str).str.contains(search_term, case=False) |
            summary_df['vendor_name'].str.contains(search_term, case=False)
        ]
    else:
        filtered_summary = summary_df
    
    # Display table with formatting
    st.dataframe(
        filtered_summary.style.format({
            'should_collect': '฿{:,.2f}',
            'actually_collected': '฿{:,.2f}',
            'difference': '฿{:,.2f}',
            'variance_pct': '{:.2f}%'
        }).background_gradient(subset=['difference'], cmap='RdYlGn'),
        use_container_width=True,
        height=400
    )


def display_vendor_details(reconciliation_df):
    """แสดงรายละเอียดตาม Vendor"""
    
    st.markdown("### 🔍 รายละเอียดตาม Vendor")
    
    # Filters
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Vendor selector
        vendors = reconciliation_df['vendor_code'].unique()
        selected_vendor = st.selectbox(
            "เลือก Vendor",
            options=sorted(vendors),
            format_func=lambda x: f"{x} - {reconciliation_df[reconciliation_df['vendor_code']==x]['vendor_name'].iloc[0]}"
        )
    
    with col2:
        # Status filter
        status_options = ['ทั้งหมด'] + list(reconciliation_df['status'].unique())
        selected_status = st.selectbox("สถานะ", status_options)
    
    # Filter data
    vendor_data = reconciliation_df[reconciliation_df['vendor_code'] == selected_vendor]
    
    if selected_status != 'ทั้งหมด':
        vendor_data = vendor_data[vendor_data['status'] == selected_status]
    
    # Vendor summary
    st.markdown("---")
    st.markdown(f"#### 📊 สรุป: {vendor_data['vendor_name'].iloc[0]}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "จำนวนหมวดหมู่",
            len(vendor_data)
        )
    
    with col2:
        st.metric(
            "ควรเรียกเก็บ",
            f"฿{vendor_data['should_collect'].sum():,.0f}"
        )
    
    with col3:
        st.metric(
            "เรียกเก็บจริง",
            f"฿{vendor_data['actually_collected'].sum():,.0f}"
        )
    
    with col4:
        diff = vendor_data['difference'].sum()
        st.metric(
            "ส่วนต่าง",
            f"฿{diff:,.0f}",
            delta=f"{diff:,.0f}",
            delta_color="inverse" if diff < 0 else "normal"
        )
    
    st.markdown("---")
    
    # Chart: Allowance breakdown
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("##### 📊 การกระจายตามหมวดหมู่")
        fig_cat = go.Figure(data=[
            go.Bar(
                x=vendor_data['category_code'],
                y=vendor_data['should_collect'],
                name='ควรเรียกเก็บ',
                marker_color='#2196F3'
            ),
            go.Bar(
                x=vendor_data['category_code'],
                y=vendor_data['actually_collected'],
                name='เรียกเก็บจริง',
                marker_color='#4CAF50'
            )
        ])
        fig_cat.update_layout(
            barmode='group',
            xaxis_title="หมวดหมู่",
            yaxis_title="จำนวนเงิน (บาท)",
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        st.markdown("##### 📈 ส่วนต่างตามหมวดหมู่")
        fig_diff = go.Figure(data=[
            go.Bar(
                x=vendor_data['category_code'],
                y=vendor_data['difference'],
                marker_color=vendor_data['difference'].apply(
                    lambda x: '#4CAF50' if x >= 0 else '#F44336'
                ),
                text=vendor_data['difference'].apply(lambda x: f'฿{x:,.0f}'),
                textposition='outside'
            )
        ])
        fig_diff.update_layout(
            xaxis_title="หมวดหมู่",
            yaxis_title="ส่วนต่าง (บาท)",
            height=300,
            showlegend=False
        )
        fig_diff.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_diff, use_container_width=True)
    
    # Detailed table
    st.markdown("---")
    st.markdown("##### 📋 รายละเอียดแต่ละหมวดหมู่")
    
    st.dataframe(
        vendor_data[[
            'category_code', 'category_name', 'should_collect',
            'actually_collected', 'difference', 'status', 'variance_pct'
        ]].style.format({
            'should_collect': '฿{:,.2f}',
            'actually_collected': '฿{:,.2f}',
            'difference': '฿{:,.2f}',
            'variance_pct': '{:.2f}%'
        }).applymap(
            lambda x: 'background-color: #ffebee' if x == '❌ ขาด' else 
                     ('background-color: #fff3e0' if x == '⚠️ เกิน' else 
                      'background-color: #e8f5e9'),
            subset=['status']
        ),
        use_container_width=True
    )
    
    # Quick export for this vendor
    st.markdown("---")
    csv_data = vendor_data.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=f"📥 Export ข้อมูล {selected_vendor}",
        data=csv_data,
        file_name=f"Vendor_{selected_vendor}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        use_container_width=True
    )


def display_analysis(summary_df, reconciliation_df):
    """แสดงการวิเคราะห์"""
    
    st.markdown("### 📈 การวิเคราะห์เชิงลึก")
    
    # Analysis options
    analysis_type = st.selectbox(
        "เลือกประเภทการวิเคราะห์",
        [
            "วิเคราะห์ Variance",
            "การกระจายตามหมวดหมู่",
            "Vendor ที่มีปัญหา",
            "เปรียบเทียบ Performance"
        ]
    )
    
    st.markdown("---")
    
    if analysis_type == "วิเคราะห์ Variance":
        analyze_variance(summary_df, reconciliation_df)
    
    elif analysis_type == "การกระจายตามหมวดหมู่":
        analyze_category_distribution(reconciliation_df)
    
    elif analysis_type == "Vendor ที่มีปัญหา":
        analyze_problematic_vendors(summary_df, reconciliation_df)
    
    elif analysis_type == "เปรียบเทียบ Performance":
        analyze_performance(summary_df)


def analyze_variance(summary_df, reconciliation_df):
    """วิเคราะห์ Variance"""
    
    st.markdown("#### 📊 การกระจายของส่วนต่าง (Variance)")
    
    # Histogram
    fig_hist = go.Figure(data=[
        go.Histogram(
            x=summary_df['variance_pct'],
            nbinsx=30,
            marker_color='#2196F3'
        )
    ])
    fig_hist.update_layout(
        xaxis_title="Variance (%)",
        yaxis_title="จำนวน Vendor",
        height=400
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Variance เฉลี่ย", f"{summary_df['variance_pct'].mean():.2f}%")
    
    with col2:
        st.metric("Variance สูงสุด", f"{summary_df['variance_pct'].max():.2f}%")
    
    with col3:
        st.metric("Variance ต่ำสุด", f"{summary_df['variance_pct'].min():.2f}%")
    
    # Vendors with high variance
    st.markdown("##### ⚠️ Vendor ที่มี Variance สูง (> 10%)")
    high_variance = summary_df[abs(summary_df['variance_pct']) > 10].sort_values('variance_pct', ascending=False)
    
    if not high_variance.empty:
        st.dataframe(
            high_variance.style.format({
                'should_collect': '฿{:,.2f}',
                'actually_collected': '฿{:,.2f}',
                'difference': '฿{:,.2f}',
                'variance_pct': '{:.2f}%'
            }),
            use_container_width=True
        )
    else:
        st.success("✅ ไม่มี Vendor ที่มี Variance เกิน 10%")


def analyze_category_distribution(reconciliation_df):
    """วิเคราะห์การกระจายตามหมวดหมู่"""
    
    st.markdown("#### 📊 การกระจายตามหมวดหมู่ Allowance")
    
    # Group by category
    category_summary = reconciliation_df.groupby('category_code').agg({
        'should_collect': 'sum',
        'actually_collected': 'sum',
        'difference': 'sum'
    }).reset_index()
    
    category_summary = category_summary.sort_values('should_collect', ascending=False)
    
    # Chart
    fig = go.Figure(data=[
        go.Bar(
            name='ควรเรียกเก็บ',
            x=category_summary['category_code'],
            y=category_summary['should_collect'],
            marker_color='#2196F3'
        ),
        go.Bar(
            name='เรียกเก็บจริง',
            x=category_summary['category_code'],
            y=category_summary['actually_collected'],
            marker_color='#4CAF50'
        )
    ])
    
    fig.update_layout(
        barmode='group',
        xaxis_title="หมวดหมู่",
        yaxis_title="จำนวนเงิน (บาท)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    st.markdown("##### 📋 สรุปตามหมวดหมู่")
    st.dataframe(
        category_summary.style.format({
            'should_collect': '฿{:,.2f}',
            'actually_collected': '฿{:,.2f}',
            'difference': '฿{:,.2f}'
        }),
        use_container_width=True
    )


def analyze_problematic_vendors(summary_df, reconciliation_df):
    """วิเคราะห์ Vendor ที่มีปัญหา"""
    
    st.markdown("#### ⚠️ Vendor ที่มีปัญหา")
    
    # Define problematic vendors
    problem_vendors = summary_df[summary_df['status'].isin(['❌ ขาด', '⚠️ เกิน'])]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Vendor ที่เรียกเก็บไม่ครบ",
            len(summary_df[summary_df['status'] == '❌ ขาด'])
        )
    
    with col2:
        st.metric(
            "Vendor ที่เรียกเก็บเกิน",
            len(summary_df[summary_df['status'] == '⚠️ เกิน'])
        )
    
    st.markdown("---")
    
    # Tabs for different problem types
    tab1, tab2 = st.tabs(["❌ เรียกเก็บไม่ครบ", "⚠️ เรียกเก็บเกิน"])
    
    with tab1:
        undercollected = summary_df[summary_df['status'] == '❌ ขาด'].sort_values('difference')
        
        if not undercollected.empty:
            st.dataframe(
                undercollected.style.format({
                    'should_collect': '฿{:,.2f}',
                    'actually_collected': '฿{:,.2f}',
                    'difference': '฿{:,.2f}',
                    'variance_pct': '{:.2f}%'
                }).background_gradient(subset=['difference'], cmap='Reds'),
                use_container_width=True
            )
            
            # Total impact
            total_missing = abs(undercollected['difference'].sum())
            st.error(f"💰 ยอดรวมที่เรียกเก็บไม่ครบ: ฿{total_missing:,.2f}")
        else:
            st.success("✅ ไม่มี Vendor ที่เรียกเก็บไม่ครบ")
    
    with tab2:
        overcollected = summary_df[summary_df['status'] == '⚠️ เกิน'].sort_values('difference', ascending=False)
        
        if not overcollected.empty:
            st.dataframe(
                overcollected.style.format({
                    'should_collect': '฿{:,.2f}',
                    'actually_collected': '฿{:,.2f}',
                    'difference': '฿{:,.2f}',
                    'variance_pct': '{:.2f}%'
                }).background_gradient(subset=['difference'], cmap='YlOrRd'),
                use_container_width=True
            )
            
            # Total impact
            total_over = overcollected['difference'].sum()
            st.warning(f"💰 ยอดรวมที่เรียกเก็บเกิน: ฿{total_over:,.2f}")
        else:
            st.success("✅ ไม่มี Vendor ที่เรียกเก็บเกิน")


def analyze_performance(summary_df):
    """วิเคราะห์ Performance"""
    
    st.markdown("#### 📊 Performance Ranking")
    
    # Calculate accuracy score
    summary_df['accuracy_score'] = 100 - abs(summary_df['variance_pct'])
    
    # Sort by accuracy
    ranked = summary_df.sort_values('accuracy_score', ascending=False).reset_index(drop=True)
    ranked['rank'] = range(1, len(ranked) + 1)
    
    # Display top and bottom performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🏆 Top 10 Performers")
        top10 = ranked.head(10)[['rank', 'vendor_code', 'vendor_name', 'accuracy_score', 'status']]
        st.dataframe(
            top10.style.format({'accuracy_score': '{:.2f}%'}),
            use_container_width=True
        )
    
    with col2:
        st.markdown("##### ⚠️ Bottom 10 Performers")
        bottom10 = ranked.tail(10)[['rank', 'vendor_code', 'vendor_name', 'accuracy_score', 'status']]
        st.dataframe(
            bottom10.style.format({'accuracy_score': '{:.2f}%'}),
            use_container_width=True
        )
    
    # Overall accuracy
    st.markdown("---")
    avg_accuracy = summary_df['accuracy_score'].mean()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Accuracy เฉลี่ย", f"{avg_accuracy:.2f}%")
    
    with col2:
        perfect_match = len(summary_df[summary_df['status'] == '✅ ครบ'])
        st.metric("Perfect Match", f"{perfect_match}/{len(summary_df)}")
    
    with col3:
        match_rate = (perfect_match / len(summary_df)) * 100
        st.metric("Match Rate", f"{match_rate:.1f}%")


def display_export_options(data):
    """แสดงตัวเลือกการ Export"""
    
    st.markdown("### 💾 Export ข้อมูล")
    
    st.info("""
    เลือกข้อมูลที่ต้องการ Export:
    - **Summary**: สรุปภาพรวมตาม Vendor
    - **Reconciliation**: รายละเอียดการเปรียบเทียบทั้งหมด
    - **Calculated**: ข้อมูลการคำนวณ Allowances
    - **All**: ทั้งหมดในไฟล์เดียว
    """)
    
    st.markdown("---")
    
    export_type = st.radio(
        "เลือกประเภทข้อมูล",
        ["Summary", "Reconciliation", "Calculated", "All"]
    )
    
    file_format = st.radio(
        "เลือกรูปแบบไฟล์",
        ["Excel (.xlsx)", "CSV (.csv)"]
    )
    
    st.markdown("---")
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if st.button("📥 Export ข้อมูล", type="primary", use_container_width=True):
        if file_format == "Excel (.xlsx)":
            export_excel(data, export_type, timestamp)
        else:
            export_csv(data, export_type, timestamp)


def export_excel(data, export_type, timestamp):
    """Export เป็น Excel"""
    import io
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if export_type == "Summary":
            data['summary'].to_excel(writer, sheet_name='Summary', index=False)
        elif export_type == "Reconciliation":
            data['reconciliation'].to_excel(writer, sheet_name='Reconciliation', index=False)
        elif export_type == "Calculated":
            data['calculated'].to_excel(writer, sheet_name='Calculated', index=False)
        else:  # All
            data['summary'].to_excel(writer, sheet_name='Summary', index=False)
            data['reconciliation'].to_excel(writer, sheet_name='Reconciliation', index=False)
            data['calculated'].to_excel(writer, sheet_name='Calculated', index=False)
    
    output.seek(0)
    
    st.download_button(
        label="📥 ดาวน์โหลด Excel",
        data=output,
        file_name=f"TTA_Export_{export_type}_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def export_csv(data, export_type, timestamp):
    """Export เป็น CSV"""
    
    if export_type == "Summary":
        csv_data = data['summary'].to_csv(index=False, encoding='utf-8-sig')
        filename = f"TTA_Summary_{timestamp}.csv"
    elif export_type == "Reconciliation":
        csv_data = data['reconciliation'].to_csv(index=False, encoding='utf-8-sig')
        filename = f"TTA_Reconciliation_{timestamp}.csv"
    elif export_type == "Calculated":
        csv_data = data['calculated'].to_csv(index=False, encoding='utf-8-sig')
        filename = f"TTA_Calculated_{timestamp}.csv"
    else:  # All - zip multiple CSV files
        st.warning("⚠️ สำหรับ CSV กรุณาเลือก export แต่ละประเภทแยกกัน")
        return
    
    st.download_button(
        label="📥 ดาวน์โหลด CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )
