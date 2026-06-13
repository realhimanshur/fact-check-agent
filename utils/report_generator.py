"""
Report Generator Module
Generates PDF and CSV reports of verification results
"""

import os
import csv
from datetime import datetime
from typing import List, Dict
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates fact-checking reports in PDF and CSV formats
    """
    
    def __init__(self):
        """Initialize report generator"""
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_pdf_report(self, results: List[Dict], source_document: str) -> str:
        """
        Generate PDF report of verification results
        
        Args:
            results: List of verification results
            source_document: Name of source PDF
            
        Returns:
            Path to generated PDF report
        """
        try:
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fact_check_report_{timestamp}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Create PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#764ba2'),
                spaceAfter=12
            )
            
            # Title
            story.append(Paragraph("🔍 Fact-Check Report", title_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # Document info
            story.append(Paragraph(f"<b>Source Document:</b> {source_document}", styles['Normal']))
            story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))
            
            # Summary statistics
            total_claims = len(results)
            verified = sum(1 for r in results if r['verdict'] == 'VERIFIED')
            inaccurate = sum(1 for r in results if r['verdict'] == 'INACCURATE')
            false = sum(1 for r in results if r['verdict'] == 'FALSE')
            
            story.append(Paragraph("Summary Statistics", heading_style))
            
            summary_data = [
                ['Total Claims', 'Verified', 'Inaccurate', 'False'],
                [str(total_claims), str(verified), str(inaccurate), str(false)]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.4 * inch))
            
            # Detailed results
            story.append(Paragraph("Detailed Verification Results", heading_style))
            story.append(Spacer(1, 0.2 * inch))
            
            for idx, result in enumerate(results, 1):
                # Claim header
                verdict = result['verdict']
                emoji = self._get_verdict_emoji(verdict)
                
                story.append(Paragraph(
                    f"<b>Claim #{idx}: {emoji} {verdict}</b>",
                    styles['Heading3']
                ))
                
                # Claim details
                story.append(Paragraph(f"<b>Claim:</b> {result['claim']}", styles['Normal']))
                story.append(Paragraph(f"<b>Type:</b> {result['type']}", styles['Normal']))
                story.append(Paragraph(f"<b>Page:</b> {result.get('page', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"<b>Confidence:</b> {result.get('confidence', 0)}%", styles['Normal']))
                
                # Reasoning
                if result.get('reasoning'):
                    story.append(Paragraph(f"<b>Analysis:</b> {result['reasoning']}", styles['Normal']))
                
                # Corrected fact
                if result.get('corrected_fact'):
                    story.append(Paragraph(
                        f"<b>Correct Information:</b> {result['corrected_fact']}",
                        styles['Normal']
                    ))
                
                # Sources
                if result.get('sources'):
                    story.append(Paragraph("<b>Sources:</b>", styles['Normal']))
                    for source_idx, source in enumerate(result['sources'][:3], 1):
                        if isinstance(source, dict):
                            story.append(Paragraph(
                                f"{source_idx}. {source.get('title', 'Source')} - {source.get('url', '')}",
                                styles['Normal']
                            ))
                
                story.append(Spacer(1, 0.3 * inch))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def generate_csv_report(self, results: List[Dict]) -> str:
        """
        Generate CSV report of verification results
        
        Args:
            results: List of verification results
            
        Returns:
            Path to generated CSV report
        """
        try:
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fact_check_report_{timestamp}.csv"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Claim',
                    'Type',
                    'Page',
                    'Verdict',
                    'Confidence',
                    'Reasoning',
                    'Corrected Fact',
                    'Evidence',
                    'Sources'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    # Format evidence
                    evidence = ' | '.join(result.get('evidence', []))
                    
                    # Format sources
                    sources = []
                    for source in result.get('sources', []):
                        if isinstance(source, dict):
                            sources.append(f"{source.get('title', '')} ({source.get('url', '')})")
                        else:
                            sources.append(str(source))
                    sources_str = ' | '.join(sources)
                    
                    writer.writerow({
                        'Claim': result['claim'],
                        'Type': result['type'],
                        'Page': result.get('page', 'N/A'),
                        'Verdict': result['verdict'],
                        'Confidence': f"{result.get('confidence', 0)}%",
                        'Reasoning': result.get('reasoning', ''),
                        'Corrected Fact': result.get('corrected_fact', ''),
                        'Evidence': evidence,
                        'Sources': sources_str
                    })
            
            logger.info(f"CSV report generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {str(e)}")
            raise
    
    def _get_verdict_emoji(self, verdict: str) -> str:
        """Get emoji for verdict"""
        emoji_map = {
            'VERIFIED': '✅',
            'INACCURATE': '⚠️',
            'FALSE': '❌',
            'ERROR': '⚫'
        }
        return emoji_map.get(verdict, '❓')