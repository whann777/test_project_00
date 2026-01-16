import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import config

def show():
    # Custom CSS
    st.markdown("""
        <style>
        .dashboard-card {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin: 1rem 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            height: 100%;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.95;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-complete { color: #43A047; font-weight: 600; }
        .status-over { color: #FB8C00; font-weight: 600; }
        .status-under { color: #E53935; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("# 📊 Dashboard Mode")
        st.markdown("### วิเคราะห์และตรวจสอบข้อมูล")
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
    
    st.markdown("---")
    
    # เช็คว่ามีข้อมูลหรือยัง
    if 'auditor_data' not in st.session_state:
        display_no_data()
        return
    
    # แสดง Dashboard
    display_dashboard()


def display_no_data():
    """แสดงหน้าเมื่อไม่มีข้อมูล"""
    
    st.markdown("""
        <div class="dashboard-card">
            <h3>ℹ️ ไม่พบข้อมูล</h3>
            <p>กรุณาเริ่มประมวลผลใน <b>Analysis Mode</b> ก่อน หรืออัปโหลดไฟล์ Excel</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📥 อัปโหลดไฟล์ Excel (Optional)")
    
    excel_file = st.file_uploader(
        "อัปโหลดไฟล์ผลลัพธ์ที่ Export จาก Analysis Mode",
        type=['xlsx'],
        help="ไฟล์ Excel ที่มี 3 sheets: Calculated, Reconciliation, Summary"
    )
    
    if excel_file:
        try:
            calculated_df = pd.read_excel(excel_file, sheet_name='Calculated')
            reconciliation_df = pd.read_excel(excel_file, sheet_name='Reconciliation')
            summary_df = pd.read_excel(excel_file, sheet_name='Summary')
            
            st.session_state.auditor_data = {
                'calculated': calculated_df,
                'reconciliation': reconciliation_df,
                'summary': summary_df,
                'upload_time': datetime.now()
            }
            
            st.success("✅ โหลดข้อมูลสำเร็จ!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")


def display_dashboard():
    """แสดง Dashboard หลัก"""
    
    data = st.session_state.auditor_data
    summary_df = data['summary']
    reconciliation_df = data['reconciliation']
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard Overview",
        "🔍 Vendor Details",
        "📈 Advanced Analysis"
    ])
    
    with tab1:
        display_overview_tab(summary_df, reconciliation_df)
    
    with tab2:
        display_vendor_tab(reconciliation_df)
    
    with tab3:
        display_analysis_tab(summary_df, reconciliation_df)


def display_overview_tab(summary_df, reconciliation_df):
    """Tab 1: Dashboard Overview"""
    
    st.markdown("### 📊 ภาพรวมทั้งหมด")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    total_should = summary_df['should_collect'].sum()
    total_actual = summary_df['actually_collected'].sum()
    total_diff = summary_df['difference'].sum()
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(summary_df)}</div>
            <div class="metric-label">Vendors</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">฿{total_should/1000000:.1f}M</div>
            <div class="metric-label">Should Collect</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">฿{total_actual/1000000:.1f}M</div>
            <div class="metric-label">Actually Collected</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color = "#43A047" if abs(total_diff) < 1000 else ("#E53935" if total_diff < 0 else "#FB8C00")
        st.markdown(f"""
        <div class="metric-card" style="background: {color};">
            <div class="metric-value">฿{total_diff/1000000:.1f}M</div>
            <div class="metric-label">Difference</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Collection Status")
        
        status_counts = summary_df['status'].value_counts()
        
        fig_status = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.5,
            marker_colors=['#43A047', '#FB8C00', '#E53935'],
            textinfo='label+percent',
            textfont_size=13
        )])
        fig_status.update_layout(
            showlegend=True,
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_status, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 💰 Top 10 Vendors by Amount")
        
        top_vendors = summary_df.nlargest(10, 'should_collect')
        
        fig_top = go.Figure(data=[
            go.Bar(
                y=top_vendors['vendor_name'],
                x=top_vendors['should_collect'],
                orientation='h',
                text=top_vendors['should_collect'].apply(lambda x: f'฿{x/1000000:.1f}M'),
                textposition='auto',
                marker_color='#667eea',
                hovertemplate='<b>%{y}</b><br>฿%{x:,.0f}<extra></extra>'
            )
        ])
        fig_top.update_layout(
            showlegend=False,
            height=350,
            xaxis_title="Amount (THB)",
            yaxis_title="",
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_top, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Variance Distribution
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📈 Variance Distribution")
    
    fig_variance = go.Figure(data=[
        go.Histogram(
            x=summary_df['variance_pct'],
            nbinsx=30,
            marker_color='#667eea',
            opacity=0.8,
            hovertemplate='Variance: %{x:.1f}%<br>Count: %{y}<extra></extra>'
        )
    ])
    fig_variance.update_layout(
        xaxis_title="Variance (%)",
        yaxis_title="Number of Vendors",
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
        showlegend=False
    )
    fig_variance.add_vline(x=0, line_dash="dash", line_color="red", opacity=0.5)
    st.plotly_chart(fig_variance, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary Table
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Summary Table")
    
    # Search
    search_term = st.text_input("🔍 Search Vendor", placeholder="Enter vendor code or name...")
    
    filtered_summary = summary_df
    if search_term:
        filtered_summary = summary_df[
            summary_df['vendor_code'].astype(str).str.contains(search_term, case=False) |
            summary_df['vendor_name'].str.contains(search_term, case=False)
        ]
    
    # Display table
    st.dataframe(
        filtered_summary.style.format({
            'should_collect': '฿{:,.0f}',
            'actually_collected': '฿{:,.0f}',
            'difference': '฿{:,.0f}',
            'variance_pct': '{:.2f}%'
        }).applymap(
            lambda x: 'color: #43A047; font-weight: 600' if x == '✅ ครบ' else 
                     ('color: #FB8C00; font-weight: 600' if x == '⚠️ เกิน' else 
                      'color: #E53935; font-weight: 600'),
            subset=['status']
        ),
        use_container_width=True,
        height=400
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Export Section
    st.markdown("---")
    display_export_section(summary_df, reconciliation_df)


def display_vendor_tab(reconciliation_df):
    """Tab 2: Vendor Details"""
    
    st.markdown("### 🔍 Vendor Analysis")
    
    # Vendor Selector
    vendors = sorted(reconciliation_df['vendor_code'].unique())
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_vendor = st.selectbox(
            "Select Vendor",
            options=vendors,
            format_func=lambda x: f"{x} - {reconciliation_df[reconciliation_df['vendor_code']==x]['vendor_name'].iloc[0]}"
        )
    
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            options=['All', '✅ ครบ', '⚠️ เกิน', '❌ ขาด']
        )
    
    # Filter data
    vendor_data = reconciliation_df[reconciliation_df['vendor_code'] == selected_vendor].copy()
    
    if status_filter != 'All':
        vendor_data = vendor_data[vendor_data['status'] == status_filter]
    
    # Vendor Summary
    st.markdown(f"### {vendor_data['vendor_name'].iloc[0]}")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Categories", len(vendor_data))
    
    with col2:
        should = vendor_data['should_collect'].sum()
        st.metric("Should Collect", f"฿{should:,.0f}")
    
    with col3:
        actual = vendor_data['actually_collected'].sum()
        st.metric("Actually Collected", f"฿{actual:,.0f}")
    
    with col4:
        diff = vendor_data['difference'].sum()
        st.metric("Difference", f"฿{diff:,.0f}", delta=f"{diff:,.0f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 By Category")
        
        fig_cat = go.Figure(data=[
            go.Bar(
                name='Should Collect',
                x=vendor_data['category_code'],
                y=vendor_data['should_collect'],
                marker_color='#667eea'
            ),
            go.Bar(
                name='Actually Collected',
                x=vendor_data['category_code'],
                y=vendor_data['actually_collected'],
                marker_color='#43A047'
            )
        ])
        fig_cat.update_layout(
            barmode='group',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3)
        )
        st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 Variance by Category")
        
        # Sort by absolute variance
        vendor_data_sorted = vendor_data.sort_values('difference', key=abs, ascending=False)
        
        colors = vendor_data_sorted['difference'].apply(
            lambda x: '#43A047' if x >= -1 else '#E53935'
        )
        
        fig_diff = go.Figure(data=[
            go.Bar(
                x=vendor_data_sorted['category_code'],
                y=vendor_data_sorted['difference'],
                marker_color=colors,
                text=vendor_data_sorted['difference'].apply(lambda x: f'฿{x:,.0f}'),
                textposition='outside'
            )
        ])
        fig_diff.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        fig_diff.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_diff, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Detail Table
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Detailed Breakdown")
    
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
            lambda x: 'color: #43A047; font-weight: 600' if x == '✅ ครบ' else 
                     ('color: #FB8C00; font-weight: 600' if x == '⚠️ เกิน' else 
                      'color: #E53935; font-weight: 600'),
            subset=['status']
        ),
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Export this vendor
    st.markdown("---")
    csv_data = vendor_data.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=f"📥 Export {selected_vendor} Data",
        data=csv_data,
        file_name=f"Vendor_{selected_vendor}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        use_container_width=True
    )


def display_analysis_tab(summary_df, reconciliation_df):
    """Tab 3: Advanced Analysis"""
    
    st.markdown("### 📈 Advanced Analytics")
    
    analysis_type = st.selectbox(
        "Select Analysis Type",
        [
            "Variance Analysis",
            "Category Distribution",
            "Problem Vendors",
            "Performance Ranking"
        ]
    )
    
    st.markdown("---")
    
    if analysis_type == "Variance Analysis":
        analyze_variance(summary_df)
    elif analysis_type == "Category Distribution":
        analyze_categories(reconciliation_df)
    elif analysis_type == "Problem Vendors":
        analyze_problems(summary_df)
    elif analysis_type == "Performance Ranking":
        analyze_performance(summary_df)


def analyze_variance(summary_df):
    """Variance Analysis"""
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📊 Variance Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average Variance", f"{summary_df['variance_pct'].mean():.2f}%")
    
    with col2:
        st.metric("Max Variance", f"{summary_df['variance_pct'].max():.2f}%")
    
    with col3:
        st.metric("Min Variance", f"{summary_df['variance_pct'].min():.2f}%")
    
    with col4:
        high_var = len(summary_df[abs(summary_df['variance_pct']) > config.HIGH_VARIANCE_THRESHOLD])
        st.metric("High Variance (>10%)", high_var)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # High variance vendors
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### ⚠️ High Variance Vendors")
    
    high_variance = summary_df[abs(summary_df['variance_pct']) > config.HIGH_VARIANCE_THRESHOLD].sort_values(
        'variance_pct', key=abs, ascending=False
    )
    
    if not high_variance.empty:
        st.dataframe(
            high_variance.style.format({
                'should_collect': '฿{:,.0f}',
                'actually_collected': '฿{:,.0f}',
                'difference': '฿{:,.0f}',
                'variance_pct': '{:.2f}%'
            }).background_gradient(subset=['variance_pct'], cmap='RdYlGn_r'),
            use_container_width=True
        )
    else:
        st.success("✅ No vendors with variance > 10%")
    
    st.markdown('</div>', unsafe_allow_html=True)


def analyze_categories(reconciliation_df):
    """Category Analysis"""
    
    category_summary = reconciliation_df.groupby('category_code').agg({
        'should_collect': 'sum',
        'actually_collected': 'sum',
        'difference': 'sum'
    }).reset_index()
    
    category_summary = category_summary.sort_values('should_collect', ascending=False)
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📊 Collection by Category")
    
    fig = go.Figure(data=[
        go.Bar(
            name='Should Collect',
            x=category_summary['category_code'],
            y=category_summary['should_collect'],
            marker_color='#667eea'
        ),
        go.Bar(
            name='Actually Collected',
            x=category_summary['category_code'],
            y=category_summary['actually_collected'],
            marker_color='#43A047'
        )
    ])
    
    fig.update_layout(
        barmode='group',
        height=400,
        margin=dict(l=20, r=20, t=20, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Table
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Category Summary")
    
    st.dataframe(
        category_summary.style.format({
            'should_collect': '฿{:,.0f}',
            'actually_collected': '฿{:,.0f}',
            'difference': '฿{:,.0f}'
        }),
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


def analyze_problems(summary_df):
    """Problem Vendors Analysis"""
    
    undercollected = summary_df[summary_df['status'] == '❌ ขาด'].sort_values('difference')
    overcollected = summary_df[summary_df['status'] == '⚠️ เกิน'].sort_values('difference', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### ❌ Under-collected")
        st.metric("Count", len(undercollected))
        
        if not undercollected.empty:
            total_missing = abs(undercollected['difference'].sum())
            st.metric("Total Missing", f"฿{total_missing:,.0f}")
            
            st.dataframe(
                undercollected.style.format({
                    'should_collect': '฿{:,.0f}',
                    'actually_collected': '฿{:,.0f}',
                    'difference': '฿{:,.0f}',
                    'variance_pct': '{:.2f}%'
                }),
                use_container_width=True,
                height=300
            )
        else:
            st.success("✅ No under-collections")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### ⚠️ Over-collected")
        st.metric("Count", len(overcollected))
        
        if not overcollected.empty:
            total_over = overcollected['difference'].sum()
            st.metric("Total Over", f"฿{total_over:,.0f}")
            
            st.dataframe(
                overcollected.style.format({
                    'should_collect': '฿{:,.0f}',
                    'actually_collected': '฿{:,.0f}',
                    'difference': '฿{:,.0f}',
                    'variance_pct': '{:.2f}%'
                }),
                use_container_width=True,
                height=300
            )
        else:
            st.success("✅ No over-collections")
        
        st.markdown('</div>', unsafe_allow_html=True)


def analyze_performance(summary_df):
    """Performance Ranking"""
    
    summary_df_copy = summary_df.copy()
    summary_df_copy['accuracy_score'] = 100 - abs(summary_df_copy['variance_pct'])
    ranked = summary_df_copy.sort_values('accuracy_score', ascending=False).reset_index(drop=True)
    ranked['rank'] = range(1, len(ranked) + 1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 🏆 Top 10 Performers")
        
        top10 = ranked.head(10)[['rank', 'vendor_code', 'vendor_name', 'accuracy_score', 'status']]
        st.dataframe(
            top10.style.format({'accuracy_score': '{:.2f}%'}),
            use_container_width=True,
            height=400
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### ⚠️ Bottom 10 Performers")
        
        bottom10 = ranked.tail(10)[['rank', 'vendor_code', 'vendor_name', 'accuracy_score', 'status']]
        st.dataframe(
            bottom10.style.format({'accuracy_score': '{:.2f}%'}),
            use_container_width=True,
            height=400
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Overall metrics
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📊 Overall Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_accuracy = summary_df_copy['accuracy_score'].mean()
        st.metric("Average Accuracy", f"{avg_accuracy:.2f}%")
    
    with col2:
        perfect_match = len(summary_df[summary_df['status'] == '✅ ครบ'])
        st.metric("Perfect Matches", f"{perfect_match}/{len(summary_df)}")
    
    with col3:
        match_rate = (perfect_match / len(summary_df)) * 100
        st.metric("Match Rate", f"{match_rate:.1f}%")
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_export_section(summary_df, reconciliation_df):
    """Export Section"""
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("### 💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_type = st.selectbox(
            "Select Data to Export",
            ["Summary", "Detailed Reconciliation", "Both (Excel)"]
        )
    
    with col2:
        file_format = st.selectbox(
            "File Format",
            ["Excel (.xlsx)", "CSV (.csv)"]
        )
    
    if st.button("📥 Generate Export", type="primary", use_container_width=True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if file_format == "Excel (.xlsx)":
            import io
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if export_type in ["Summary", "Both (Excel)"]:
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                if export_type in ["Detailed Reconciliation", "Both (Excel)"]:
                    reconciliation_df.to_excel(writer, sheet_name='Details', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 Download Excel",
                data=output,
                file_name=f"TTA_Export_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            if export_type == "Summary":
                csv_data = summary_df.to_csv(index=False, encoding='utf-8-sig')
                filename = f"TTA_Summary_{timestamp}.csv"
            else:
                csv_data = reconciliation_df.to_csv(index=False, encoding='utf-8-sig')
                filename = f"TTA_Details_{timestamp}.csv"
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=filename,
                mime='text/csv',
                use_container_width=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
