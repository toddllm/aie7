#!/usr/bin/env python3
"""Create a test PDF for demonstrating PDF support in RAG"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import textwrap

def create_test_pdf():
    # Create PDF
    c = canvas.Canvas("data/rag_enhancement_test.pdf", pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "RAG System Enhancement: PDF Support Documentation")
    
    # Content
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    content = [
        ("Overview", [
            "This document demonstrates the PDF support enhancement added to our Retrieval Augmented Generation (RAG) system.",
            "The system can now process both text files and PDF documents, extracting content for embedding and retrieval."
        ]),
        ("Key Features", [
            "1. Universal Document Loader: Handles both .txt and .pdf files seamlessly",
            "2. Page-aware extraction: PDF content includes page numbers for reference",
            "3. Directory scanning: Can process entire directories with mixed file types",
            "4. Error handling: Gracefully handles corrupted or unreadable PDFs"
        ]),
        ("Implementation Details", [
            "The PDF support uses the pypdf library for robust PDF text extraction.",
            "Text is extracted page by page and formatted with page markers.",
            "The UniversalLoader class provides a unified interface for all document types."
        ]),
        ("Distance Metrics", [
            "Currently, the system uses cosine similarity for vector comparison.",
            "Future enhancements could include Euclidean distance, Manhattan distance, or dot product similarity.",
            "Each metric has different properties suitable for various use cases."
        ])
    ]
    
    for section_title, section_content in content:
        # Section title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(inch, y_position, section_title)
        y_position -= 0.3*inch
        
        # Section content
        c.setFont("Helvetica", 11)
        for paragraph in section_content:
            # Wrap text
            wrapped_text = textwrap.wrap(paragraph, width=70)
            for line in wrapped_text:
                c.drawString(1.2*inch, y_position, line)
                y_position -= 0.2*inch
            y_position -= 0.1*inch
        
        y_position -= 0.2*inch
        
        # Check if we need a new page
        if y_position < inch:
            c.showPage()
            y_position = height - inch
    
    # Save the PDF
    c.save()
    print("Test PDF created: data/rag_enhancement_test.pdf")

if __name__ == "__main__":
    try:
        create_test_pdf()
    except ImportError:
        print("Installing reportlab for PDF creation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"])
        create_test_pdf()