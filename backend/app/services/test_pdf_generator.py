import pytest
from jinja2.exceptions import TemplateNotFound

from app.utils.pdf_generator import generate_pdf_from_data

MOCK_CV_DATA = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "summary": "A test summary.",
    "experience": [
        {"title": "Test Engineer", "company": "TestCo", "dates": "2020-Present", "description": ["Did a test."]}
    ],
    "skills": ["Testing", "Pytest"],
    "education": [
        {"degree": "B.S. in Testing", "institution": "Test University", "year": "2020"}
    ]
}

def test_generate_pdf_from_data_modern_template():
    """
    Tests successful PDF generation with the modern template and mock data.
    """
    pdf_bytes = generate_pdf_from_data(MOCK_CV_DATA, "cv_template_modern.html")

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF-'), "Output should be a valid PDF file"

def test_generate_pdf_with_nonexistent_template():
    """
    Tests that a TemplateNotFound error is raised when the template does not exist.
    """
    with pytest.raises(TemplateNotFound):
        generate_pdf_from_data(MOCK_CV_DATA, "nonexistent_template.html")