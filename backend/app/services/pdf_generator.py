import io
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
import logging

# Configure logging
logger = logging.getLogger(__name__)

def generate_pdf_from_data(cv_data: Dict[str, Any], template_name: str = "modern") -> bytes:
    """
    Generates a PDF from structured CV data using ReportLab.

    Args:
        cv_data: A dictionary containing the tailored CV content from CVTailor.
        template_name: The template style to use ('modern' or 'classic').

    Returns:
        A byte stream representing the generated PDF file.
    """
    try:
        logger.info(f"Generating PDF with template: {template_name}")
        
        # Create a buffer to hold the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document with tighter margins for 1-page fit
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        # Compact styles for 1-page fit
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=HexColor('#2c3e50'),
            spaceAfter=3,
            spaceBefore=0,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=HexColor('#3498db'),
            spaceAfter=2,
            spaceBefore=6
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=10,
            textColor=HexColor('#2c3e50'),
            spaceAfter=1,
            spaceBefore=3
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=9,
            textColor=HexColor('#34495e'),
            spaceAfter=2,
            leading=11
        )
        
        contact_style = ParagraphStyle(
            'CustomContact',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#7f8c8d'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        # Add Name (Title)
        name = cv_data.get('personal_info', {}).get('name', 'Your Name')
        elements.append(Paragraph(name, title_style))
        
        # Add Contact Information
        contact_info = cv_data.get('personal_info', {})
        contact_parts = []
        if contact_info.get('email'):
            contact_parts.append(contact_info['email'])
        if contact_info.get('phone'):
            contact_parts.append(contact_info['phone'])
        if contact_info.get('location'):
            contact_parts.append(contact_info['location'])
        
        if contact_parts:
            elements.append(Paragraph(' | '.join(contact_parts), contact_style))
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Add Summary
        summary = cv_data.get('summary', '')
        if summary:
            elements.append(Paragraph('Professional Summary', heading_style))
            elements.append(Paragraph(summary, body_style))
            elements.append(Spacer(1, 0.05*inch))
        
        # Add Experience
        experience = cv_data.get('experience', [])
        if experience and isinstance(experience, list) and len(experience) > 0:
            # Filter out empty or invalid entries
            valid_experience = [e for e in experience if isinstance(e, dict) and (e.get('title') or e.get('company') or e.get('description'))]
            
            if valid_experience:
                elements.append(Paragraph('Professional Experience', heading_style))
                for exp in valid_experience:
                    # Job title and company
                    title = exp.get('title', 'Position')
                    company = exp.get('company', 'Company')
                    dates = exp.get('dates', '')
                    
                    job_header = f"<b>{title}</b> at {company}"
                    if dates:
                        job_header += f" ({dates})"
                    elements.append(Paragraph(job_header, subheading_style))
                    
                    # Description
                    description = exp.get('description', '')
                    if description:
                        # Handle both string and list
                        if isinstance(description, list):
                            # Display each bullet point separately
                            for bullet in description:
                                if bullet and str(bullet).strip():
                                    elements.append(Paragraph(f"• {bullet}", body_style))
                        else:
                            elements.append(Paragraph(str(description), body_style))
                    
                    # Achievements
                    achievements = exp.get('achievements', [])
                    if achievements:
                        for achievement in achievements:
                            elements.append(Paragraph(f"• {achievement}", body_style))
                    
                    elements.append(Spacer(1, 0.05*inch))
        elif isinstance(experience, str) and experience.strip():
            # Handle experience as a single string
            elements.append(Paragraph('Professional Experience', heading_style))
            elements.append(Paragraph(experience, body_style))
            elements.append(Spacer(1, 0.05*inch))
        
        # Add Education
        education = cv_data.get('education', [])
        if education:
            elements.append(Paragraph('Education', heading_style))
            for edu in education:
                # Handle different education formats
                if isinstance(edu, dict):
                    degree = edu.get('degree', '')
                    field = edu.get('field', '') or edu.get('major', '')
                    institution = edu.get('institution', 'Institution')
                    dates = edu.get('dates', '') or edu.get('year', '')
                    
                    # Format: "B.Sc in Computer Science - Institution (2020)"
                    if field and degree:
                        edu_header = f"<b>{degree} in {field}</b> - {institution}"
                    elif degree:
                        edu_header = f"<b>{degree}</b> - {institution}"
                    else:
                        edu_header = f"<b>{institution}</b>"
                    
                    if dates:
                        edu_header += f" ({dates})"
                    elements.append(Paragraph(edu_header, subheading_style))
                    
                    details = edu.get('details', '')
                    if details:
                        elements.append(Paragraph(details, body_style))
                else:
                    # Handle string format
                    elements.append(Paragraph(str(edu), subheading_style))
                
                elements.append(Spacer(1, 0.03*inch))
        
        # Add Skills
        skills = cv_data.get('skills', [])
        if skills:
            elements.append(Paragraph('Skills', heading_style))
            # Handle different skill formats
            if isinstance(skills, dict):
                # If skills is a dict with categories
                for category, skill_list in skills.items():
                    if isinstance(skill_list, list) and len(skill_list) > 0:
                        category_skills = ', '.join(str(s) for s in skill_list)
                        elements.append(Paragraph(f"<b>{category.replace('_', ' ').title()}:</b> {category_skills}", body_style))
                    elif skill_list and not isinstance(skill_list, list):
                        elements.append(Paragraph(f"<b>{category.replace('_', ' ').title()}:</b> {skill_list}", body_style))
            elif isinstance(skills, list):
                # Filter out placeholder text
                real_skills = [s for s in skills if s and not ('•' in str(s) and len(str(s)) < 50)]
                if real_skills:
                    skills_text = ' • '.join(str(s) for s in real_skills)
                    elements.append(Paragraph(skills_text, body_style))
            else:
                elements.append(Paragraph(str(skills), body_style))
            elements.append(Spacer(1, 0.05*inch))
        
        # Add Certifications
        certifications = cv_data.get('certifications', [])
        if certifications:
            elements.append(Paragraph('Certifications', heading_style))
            for cert in certifications:
                cert_text = cert.get('name', cert) if isinstance(cert, dict) else cert
                elements.append(Paragraph(f"• {cert_text}", body_style))
            elements.append(Spacer(1, 0.03*inch))
        
        # Build PDF
        doc.build(elements)
        
        # Get the PDF data
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info("Successfully generated PDF byte stream.")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"An error occurred during PDF generation: {e}")
        raise