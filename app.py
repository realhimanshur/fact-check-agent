"""
Fact-Check Agent - Main Application
Production-ready web application for automated fact verification
"""

import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import os
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.pdf_reader import PDFReader
from utils.claim_extractor import ClaimExtractor
from utils.search_engine import SearchEngine
from utils.verifier import FactVerifier
from utils.report_generator import ReportGenerator
from utils.helpers import (
    validate_pdf_file,
    create_directories,
    save_uploaded_file,
    format_confidence_score,
    get_verdict_emoji,
    get_verdict_color
)

# Page configuration
st.set_page_config(
    page_title="Fact-Check Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #6c757d;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .claim-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .verified {
        border-left: 4px solid #28a745;
    }
    .inaccurate {
        border-left: 4px solid #ffc107;
    }
    .false {
        border-left: 4px solid #dc3545;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = None

# Create necessary directories
create_directories()

def home_page():
    """Display home page with application overview"""
    st.markdown('<div class="main-header">🔍 Fact-Check Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your AI-Powered Truth Layer for Document Verification</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📄 Upload Documents
        - Drag and drop PDF files
        - Multi-page support
        - Instant text extraction
        - Secure processing
        """)
    
    with col2:
        st.markdown("""
        ### 🤖 AI Verification
        - Automatic claim extraction
        - Live web search
        - Real-time fact-checking
        - Evidence collection
        """)
    
    with col3:
        st.markdown("""
        ### 📊 Detailed Reports
        - Verification dashboard
        - Visual analytics
        - PDF/CSV export
        - Source attribution
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ## 🎯 How It Works
    
    1. **Upload PDF** - Upload any PDF document containing factual claims
    2. **AI Extraction** - Our AI extracts all factual claims automatically
    3. **Live Verification** - Each claim is verified against current web sources
    4. **Get Results** - Review detailed verdicts with evidence and sources
    5. **Export Report** - Download comprehensive PDF or CSV reports
    
    ## 🔍 What We Verify
    
    - ✅ **Numerical Claims**: Revenue, statistics, population figures
    - ✅ **Percentage Claims**: Growth rates, market share, conversions
    - ✅ **Date Claims**: Historical events, founding dates
    - ✅ **Financial Claims**: Valuations, earnings, investments
    - ✅ **Technical Claims**: Specifications, performance metrics
    
    ## 🎨 Verification Categories
    
    - **✅ VERIFIED** - Claim matches reliable current sources
    - **⚠️ INACCURATE** - Claim is outdated or partially incorrect
    - **❌ FALSE** - No reliable evidence supports the claim
    
    ## 🚀 Ready to Start?
    
    Navigate to **📤 Upload & Verify** from the sidebar to begin fact-checking!
    """)
    
    st.info("💡 **Tip**: This application uses live web search to verify claims, ensuring you get the most current and accurate information.")

def upload_page():
    """PDF upload and processing page"""
    st.markdown('<div class="main-header">📤 Upload & Verify</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload your PDF document for automated fact verification</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document containing factual claims to verify"
    )
    
    if uploaded_file is not None:
        # Validate file
        is_valid, message = validate_pdf_file(uploaded_file)
        
        if not is_valid:
            st.error(f"❌ {message}")
            return
        
        st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
        
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
        with col3:
            st.metric("File Type", "PDF")
        
        st.markdown("---")
        
        # Process button
        if st.button("🚀 Start Fact-Checking", key="process_btn"):
            process_pdf(uploaded_file)
    
    else:
        st.info("👆 Please upload a PDF file to begin")
        
        # Example use cases
        with st.expander("📋 Example Use Cases"):
            st.markdown("""
            This tool is perfect for verifying:
            
            - **Business Reports**: Company statistics, financial data, market claims
            - **Research Papers**: Statistical claims, historical facts, numerical data
            - **News Articles**: Current events, demographic data, economic figures
            - **Marketing Materials**: Product claims, performance metrics, testimonials
            - **Academic Documents**: Historical dates, scientific facts, citations
            """)

def process_pdf(uploaded_file):
    """Process uploaded PDF and perform fact-checking"""
    
    try:
        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Save file
        status_text.text("📁 Saving uploaded file...")
        progress_bar.progress(10)
        file_path = save_uploaded_file(uploaded_file)
        st.session_state.uploaded_filename = uploaded_file.name
        
        # Step 2: Extract text
        status_text.text("📄 Extracting text from PDF...")
        progress_bar.progress(20)
        pdf_reader = PDFReader()
        pdf_text, page_count = pdf_reader.extract_text(file_path)
        
        if not pdf_text or len(pdf_text.strip()) < 50:
            st.error("❌ No readable text found in PDF. Please upload a PDF with text content.")
            progress_bar.empty()
            status_text.empty()
            return
        
        st.session_state.pdf_text = pdf_text
        st.success(f"✅ Extracted text from {page_count} page(s)")
        
        # Step 3: Extract claims
        status_text.text("🤖 Extracting factual claims using AI...")
        progress_bar.progress(40)
        
        claim_extractor = ClaimExtractor()
        claims = claim_extractor.extract_claims(pdf_text, page_count)
        
        if not claims:
            st.warning("⚠️ No factual claims found in the document.")
            progress_bar.empty()
            status_text.empty()
            return
        
        st.success(f"✅ Found {len(claims)} factual claim(s)")
        
        # Step 4: Initialize search and verification
        status_text.text("🔍 Initializing search engine...")
        progress_bar.progress(50)
        
        search_engine = SearchEngine()
        verifier = FactVerifier(search_engine)
        
        # Step 5: Verify claims
        status_text.text("🔎 Verifying claims against live web sources...")
        results = []
        
        for idx, claim in enumerate(claims):
            progress = 50 + int((idx / len(claims)) * 40)
            progress_bar.progress(progress)
            status_text.text(f"🔎 Verifying claim {idx + 1} of {len(claims)}...")
            
            try:
                result = verifier.verify_claim(claim)
                results.append(result)
            except Exception as e:
                st.warning(f"⚠️ Could not verify claim: {claim['claim'][:100]}... - {str(e)}")
                # Add failed result
                results.append({
                    'claim': claim['claim'],
                    'type': claim['type'],
                    'page': claim['page'],
                    'verdict': 'ERROR',
                    'confidence': 0,
                    'evidence': [],
                    'sources': [],
                    'corrected_fact': None,
                    'reasoning': f"Verification failed: {str(e)}"
                })
        
        # Step 6: Complete
        progress_bar.progress(100)
        status_text.text("✅ Fact-checking complete!")
        
        st.session_state.results = results
        
        # Success message
        st.success(f"🎉 Successfully verified {len(results)} claims!")
        st.balloons()
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Navigate to results
        st.info("📊 View results in the **Results Dashboard** page from the sidebar")
        
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def results_page():
    """Display verification results with dashboard"""
    st.markdown('<div class="main-header">📊 Results Dashboard</div>', unsafe_allow_html=True)
    
    if st.session_state.results is None:
        st.warning("⚠️ No results available. Please upload and process a PDF first.")
        if st.button("📤 Go to Upload Page"):
            st.session_state.page = "Upload & Verify"
        return
    
    results = st.session_state.results
    
    # Calculate statistics
    total_claims = len(results)
    verified_count = sum(1 for r in results if r['verdict'] == 'VERIFIED')
    inaccurate_count = sum(1 for r in results if r['verdict'] == 'INACCURATE')
    false_count = sum(1 for r in results if r['verdict'] == 'FALSE')
    error_count = sum(1 for r in results if r['verdict'] == 'ERROR')
    
    # Header metrics
    st.markdown(f"### 📄 Document: {st.session_state.uploaded_filename or 'Unknown'}")
    st.markdown("---")
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Total Claims",
            value=total_claims,
            help="Total number of factual claims extracted"
        )
    
    with col2:
        st.metric(
            label="✅ Verified",
            value=verified_count,
            delta=f"{(verified_count/total_claims*100):.1f}%" if total_claims > 0 else "0%",
            delta_color="normal",
            help="Claims that match current reliable sources"
        )
    
    with col3:
        st.metric(
            label="⚠️ Inaccurate",
            value=inaccurate_count,
            delta=f"{(inaccurate_count/total_claims*100):.1f}%" if total_claims > 0 else "0%",
            delta_color="off",
            help="Claims that are outdated or partially incorrect"
        )
    
    with col4:
        st.metric(
            label="❌ False",
            value=false_count,
            delta=f"{(false_count/total_claims*100):.1f}%" if total_claims > 0 else "0%",
            delta_color="inverse",
            help="Claims with no reliable supporting evidence"
        )
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        if total_claims > 0:
            verdict_data = {
                'Verdict': ['Verified', 'Inaccurate', 'False', 'Error'] if error_count > 0 else ['Verified', 'Inaccurate', 'False'],
                'Count': [verified_count, inaccurate_count, false_count, error_count] if error_count > 0 else [verified_count, inaccurate_count, false_count],
                'Color': ['#28a745', '#ffc107', '#dc3545', '#6c757d'] if error_count > 0 else ['#28a745', '#ffc107', '#dc3545']
            }
            
            fig_pie = px.pie(
                verdict_data,
                values='Count',
                names='Verdict',
                title='Verification Results Distribution',
                color='Verdict',
                color_discrete_map={
                    'Verified': '#28a745',
                    'Inaccurate': '#ffc107',
                    'False': '#dc3545',
                    'Error': '#6c757d'
                }
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart
        if total_claims > 0:
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=['Verified', 'Inaccurate', 'False'] + (['Error'] if error_count > 0 else []),
                    y=[verified_count, inaccurate_count, false_count] + ([error_count] if error_count > 0 else []),
                    marker_color=['#28a745', '#ffc107', '#dc3545'] + (['#6c757d'] if error_count > 0 else []),
                    text=[verified_count, inaccurate_count, false_count] + ([error_count] if error_count > 0 else []),
                    textposition='auto'
                )
            ])
            fig_bar.update_layout(
                title='Claims by Verification Status',
                xaxis_title='Verdict',
                yaxis_title='Number of Claims',
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # Filter options
    st.markdown("### 🔍 Filter Results")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        verdict_filter = st.multiselect(
            "Filter by Verdict",
            options=['VERIFIED', 'INACCURATE', 'FALSE', 'ERROR'],
            default=['VERIFIED', 'INACCURATE', 'FALSE', 'ERROR'],
            help="Select which verdicts to display"
        )
    
    with filter_col2:
        claim_types = list(set([r['type'] for r in results]))
        type_filter = st.multiselect(
            "Filter by Claim Type",
            options=claim_types,
            default=claim_types,
            help="Select which claim types to display"
        )
    
    # Filter results
    filtered_results = [
        r for r in results
        if r['verdict'] in verdict_filter and r['type'] in type_filter
    ]
    
    st.markdown(f"### 📝 Detailed Results ({len(filtered_results)} claims)")
    
    # Display each claim
    for idx, result in enumerate(filtered_results, 1):
        verdict = result['verdict']
        emoji = get_verdict_emoji(verdict)
        color_class = get_verdict_color(verdict)
        
        with st.container():
            st.markdown(f"""
            <div class="claim-card {color_class}">
                <h4>{emoji} Claim #{idx}: {verdict}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**📄 Claim:** {result['claim']}")
                st.markdown(f"**🏷️ Type:** {result['type']}")
                st.markdown(f"**📖 Page:** {result.get('page', 'N/A')}")
            
            with col2:
                confidence = result.get('confidence', 0)
                st.metric("Confidence", format_confidence_score(confidence))
            
            # Reasoning
            if result.get('reasoning'):
                st.markdown(f"**🧠 Analysis:** {result['reasoning']}")
            
            # Corrected fact
            if result.get('corrected_fact'):
                st.warning(f"**✏️ Correct Information:** {result['corrected_fact']}")
            
            # Evidence
            if result.get('evidence'):
                with st.expander("📚 View Evidence"):
                    for ev_idx, evidence in enumerate(result['evidence'], 1):
                        st.markdown(f"**Evidence {ev_idx}:** {evidence}")
            
            # Sources
            if result.get('sources'):
                with st.expander("🔗 View Sources"):
                    for source_idx, source in enumerate(result['sources'], 1):
                        if isinstance(source, dict):
                            st.markdown(f"**{source_idx}.** [{source.get('title', 'Source')}]({source.get('url', '#')})")
                        else:
                            st.markdown(f"**{source_idx}.** {source}")
            
            st.markdown("---")
    
    # Export section
    st.markdown("### 📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF Report", key="pdf_export"):
            try:
                report_gen = ReportGenerator()
                pdf_path = report_gen.generate_pdf_report(
                    results,
                    st.session_state.uploaded_filename or "document.pdf"
                )
                
                with open(pdf_path, 'rb') as f:
                    st.download_button(
                        label="💾 Download PDF",
                        data=f.read(),
                        file_name=f"fact_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                st.success("✅ PDF report generated!")
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
    
    with col2:
        if st.button("📊 Download CSV Report", key="csv_export"):
            try:
                report_gen = ReportGenerator()
                csv_path = report_gen.generate_csv_report(results)
                
                with open(csv_path, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="💾 Download CSV",
                        data=f.read(),
                        file_name=f"fact_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                st.success("✅ CSV report generated!")
            except Exception as e:
                st.error(f"❌ Error generating CSV: {str(e)}")
    
    with col3:
        if st.button("📋 Download JSON Report", key="json_export"):
            try:
                json_data = json.dumps(results, indent=2)
                st.download_button(
                    label="💾 Download JSON",
                    data=json_data,
                    file_name=f"fact_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                st.success("✅ JSON report generated!")
            except Exception as e:
                st.error(f"❌ Error generating JSON: {str(e)}")

def main():
    """Main application entry point"""
    
    # Sidebar navigation
    st.sidebar.title("🔍 Fact-Check Agent")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "📤 Upload & Verify", "📊 Results Dashboard"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # Information
    st.sidebar.markdown("""
    ### ℹ️ About
    
    **Fact-Check Agent** is an AI-powered tool that automatically verifies factual claims in PDF documents using live web search.
    
    **Features:**
    - 📄 PDF text extraction
    - 🤖 AI claim extraction
    - 🔍 Live web verification
    - 📊 Visual analytics
    - 📥 Export reports
    
   
    
    ### 📞 Support
    
    For issues or questions, please contact "developer@example.com".
    """)
    
    st.sidebar.markdown("---")

    
    # Route to appropriate page
    if page == "🏠 Home":
        home_page()
    elif page == "📤 Upload & Verify":
        upload_page()
    elif page == "📊 Results Dashboard":
        results_page()

if __name__ == "__main__":
    main()