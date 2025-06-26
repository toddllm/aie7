"""PDF document loader for RAG system"""
import os
from typing import List
from pypdf import PdfReader
from .text_utils import TextFileLoader


class PDFLoader(TextFileLoader):
    """Loader for PDF documents that extends TextFileLoader"""
    
    def __init__(self, path: str, encoding: str = "utf-8"):
        super().__init__(path, encoding)
        
    def load(self):
        if os.path.isdir(self.path):
            self.load_directory()
        elif os.path.isfile(self.path) and self.path.lower().endswith(".pdf"):
            self.load_pdf_file()
        else:
            raise ValueError(
                "Provided path is neither a valid directory nor a .pdf file."
            )
    
    def load_pdf_file(self):
        """Load a single PDF file"""
        try:
            reader = PdfReader(self.path)
            text = ""
            
            # Extract text from all pages
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
                    
            self.documents.append(text)
            
        except Exception as e:
            print(f"Error loading PDF {self.path}: {str(e)}")
            
    def load_directory(self):
        """Load all PDF files from a directory"""
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    try:
                        reader = PdfReader(file_path)
                        text = f"--- Document: {file} ---\n"
                        
                        # Extract text from all pages
                        for page_num, page in enumerate(reader.pages):
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num + 1} ---\n"
                                text += page_text
                                
                        self.documents.append(text)
                        
                    except Exception as e:
                        print(f"Error loading PDF {file_path}: {str(e)}")


class UniversalLoader(TextFileLoader):
    """Universal loader that can handle both text and PDF files"""
    
    def __init__(self, path: str, encoding: str = "utf-8"):
        super().__init__(path, encoding)
        self.pdf_loader = PDFLoader(path, encoding)
        
    def load(self):
        if os.path.isdir(self.path):
            self.load_directory()
        elif os.path.isfile(self.path):
            if self.path.lower().endswith(".txt"):
                self.load_file()
            elif self.path.lower().endswith(".pdf"):
                self.pdf_loader.load_pdf_file()
                self.documents.extend(self.pdf_loader.documents)
            else:
                raise ValueError(
                    "File must be either .txt or .pdf format."
                )
        else:
            raise ValueError(
                "Provided path is neither a valid directory nor a file."
            )
            
    def load_directory(self):
        """Load all text and PDF files from a directory"""
        # Load text files
        super().load_directory()
        
        # Load PDF files
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    pdf_loader = PDFLoader(file_path)
                    pdf_loader.load_pdf_file()
                    self.documents.extend(pdf_loader.documents)