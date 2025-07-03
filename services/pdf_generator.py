"""
PDF Report Generator for Legal-Mind-AI
Creates professional PDF reports from agent responses
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image as RLImage
)
from reportlab.platypus.flowables import HRFlowable

class LegalMindReportGenerator:
    """
    Generate professional PDF reports for Legal-Mind-AI responses
    """
    
    def __init__(self, company_name: str = "Legal-Mind-AI", logo_path: Optional[str] = None):
        self.company_name = company_name
        self.logo_path = logo_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """
        Setup custom paragraph styles for the report
        """
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1f4e79'),
            alignment=1  # Center alignment
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#2e75b6'),
            alignment=1
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#1f4e79'),
            borderWidth=1,
            borderColor=colors.HexColor('#2e75b6'),
            borderPadding=5
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=14,
            alignment=0  # Left alignment
        ))
        
        # Executive summary
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=15,
            leading=15,
            leftIndent=20,
            rightIndent=20,
            borderWidth=1,
            borderColor=colors.HexColor('#cccccc'),
            borderPadding=10,
            backColor=colors.HexColor('#f8f9fa')
        ))
    
    def generate_report(
        self, 
        title: str, 
        content: str, 
        user_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BytesIO:
        """
        Generate a PDF report from the given content
        
        Args:
            title: Report title
            content: Main report content
            user_query: Original user query
            metadata: Additional metadata (sources, timestamps, etc.)
        
        Returns:
            BytesIO: PDF file content
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Build the report content
        story = []
        
        # Header
        story.extend(self._create_header(title))
        
        # Executive Summary
        story.extend(self._create_executive_summary(content))
        
        # Original Query
        story.extend(self._create_query_section(user_query))
        
        # Main Content
        story.extend(self._create_main_content(content))
        
        # Metadata and Sources
        if metadata:
            story.extend(self._create_metadata_section(metadata))
        
        # Footer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _create_header(self, title: str) -> list:
        """Create report header with logo and title"""
        story = []
        
        # Logo (if available)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = RLImage(self.logo_path, width=2*inch, height=0.8*inch)
                story.append(logo)
                story.append(Spacer(1, 12))
            except:
                pass  # Skip logo if there's an issue
        
        # Company name
        story.append(Paragraph(self.company_name, self.styles['ReportSubtitle']))
        
        # Report title
        story.append(Paragraph(title, self.styles['ReportTitle']))
        
        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"Generated on {date_str}", self.styles['Normal']))
        
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2e75b6')))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_executive_summary(self, content: str) -> list:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        
        # Extract first paragraph or create summary
        summary = self._extract_summary(content)
        story.append(Paragraph(summary, self.styles['ExecutiveSummary']))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_query_section(self, user_query: str) -> list:
        """Create section showing the original user query"""
        story = []
        
        story.append(Paragraph("Original Query", self.styles['SectionHeading']))
        story.append(Paragraph(f'"{user_query}"', self.styles['ReportBody']))
        story.append(Spacer(1, 15))
        
        return story
    
    def _create_main_content(self, content: str) -> list:
        """Create the main content section"""
        story = []
        
        story.append(Paragraph("Detailed Analysis", self.styles['SectionHeading']))
        
        # Split content into sections based on headers or paragraphs
        sections = self._parse_content_sections(content)
        
        for section_title, section_content in sections:
            if section_title:
                story.append(Paragraph(section_title, self.styles['Heading3']))
            
            # Split long paragraphs
            paragraphs = section_content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['ReportBody']))
                    story.append(Spacer(1, 8))
        
        return story
    
    def _create_metadata_section(self, metadata: Dict[str, Any]) -> list:
        """Create metadata and sources section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Sources and Metadata", self.styles['SectionHeading']))
        
        # Sources
        if 'sources' in metadata and metadata['sources']:
            story.append(Paragraph("Sources Referenced:", self.styles['Heading4']))
            for i, source in enumerate(metadata['sources'], 1):
                story.append(Paragraph(f"{i}. {source}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Additional metadata
        if 'agents_used' in metadata:
            story.append(Paragraph("AI Agents Consulted:", self.styles['Heading4']))
            for agent in metadata['agents_used']:
                story.append(Paragraph(f"• {agent}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Confidence and disclaimers
        disclaimer = """
        <b>Disclaimer:</b> This report was generated by Legal-Mind-AI and should be used 
        for informational purposes only. While we strive for accuracy, please verify 
        critical information with official sources and consult legal professionals for 
        specific compliance guidance.
        """
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return story
    
    def _create_footer(self) -> list:
        """Create report footer"""
        story = []
        
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        story.append(Spacer(1, 10))
        
        footer_text = f"""
        Generated by {self.company_name} | AI-Powered Legal Policy Analysis<br/>
        For questions or support, please contact your system administrator.
        """
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        return story
    
    def _extract_summary(self, content: str) -> str:
        """Extract or create a summary from the content"""
        # Simple approach: take first paragraph or first 300 characters
        paragraphs = content.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 50:
                return first_para[:300] + "..." if len(first_para) > 300 else first_para
        
        # Fallback: truncate content
        return content[:300] + "..." if len(content) > 300 else content
    
    def _parse_content_sections(self, content: str) -> list:
        """Parse content into sections based on markdown-style headers"""
        sections = []
        lines = content.split('\n')
        current_section = ""
        current_title = None
        
        for line in lines:
            line = line.strip()
            
            # Check for headers (lines starting with #, **, or all caps)
            if (line.startswith('#') or 
                (line.startswith('**') and line.endswith('**')) or
                (line.isupper() and len(line) > 5 and len(line) < 100)):
                
                # Save previous section
                if current_section.strip():
                    sections.append((current_title, current_section.strip()))
                
                # Start new section
                current_title = line.replace('#', '').replace('**', '').strip()
                current_section = ""
            else:
                current_section += line + '\n'
        
        # Add final section
        if current_section.strip():
            sections.append((current_title, current_section.strip()))
        
        # If no sections found, return content as single section
        if not sections:
            sections.append((None, content))
        
        return sections

# Global instance
report_generator = LegalMindReportGenerator(
    company_name=os.getenv("COMPANY_NAME", "Legal-Mind-AI"),
    logo_path=os.getenv("COMPANY_LOGO_PATH")
)
