#!/usr/bin/env python3
"""
Enhanced RAG script with PDF support.
This script can process both text and PDF documents.
"""

import os
import sys
from typing import List, Tuple
import numpy as np
from dotenv import load_dotenv

# Task 1: Imports and Utilities
print("Enhanced RAG with PDF Support")
print("=" * 50)
print("\nTask 1: Setting up imports and utilities...")

from aimakerspace.text_utils import CharacterTextSplitter
from aimakerspace.pdf_loader import UniversalLoader, PDFLoader
from aimakerspace.vectordatabase import VectorDatabase
import asyncio

import nest_asyncio
nest_asyncio.apply()

# Task 2: Documents
print("\nTask 2: Loading and processing documents...")

# Check if there's a specific file/directory to load
if len(sys.argv) > 1:
    data_path = sys.argv[1]
else:
    # Default to the text file
    data_path = "data/PMarcaBlogs.txt"

print(f"Loading documents from: {data_path}")

# Use UniversalLoader for both text and PDF files
try:
    loader = UniversalLoader(data_path)
    documents = loader.load_documents()
    print(f"✓ Successfully loaded {len(documents)} document(s)")
    
    # Show what types of documents were loaded
    if data_path.lower().endswith('.pdf'):
        print("  Document type: PDF")
    elif data_path.lower().endswith('.txt'):
        print("  Document type: Text")
    else:
        print("  Document type: Mixed (directory with multiple files)")
        
except Exception as e:
    print(f"❌ Error loading documents: {str(e)}")
    sys.exit(1)

# Split documents
text_splitter = CharacterTextSplitter()
split_documents = text_splitter.split_texts(documents)
print(f"✓ Split into {len(split_documents)} chunks")

# Show sample
print("\nFirst document chunk preview:")
if split_documents:
    preview = split_documents[0][:200].replace('\n', ' ')
    print(preview + "...")

# Task 3: Embeddings and Vectors
print("\nTask 3: Setting up embeddings and vector database...")

# Get OpenAI API Key
import openai

# Try to load from .env file
load_dotenv()

if "OPENAI_API_KEY" not in os.environ:
    print("\n⚠️  OpenAI API Key not found!")
    print("Please set your OpenAI API key in one of the following ways:")
    print("1. Create a .env file with: OPENAI_API_KEY=your_key_here")
    print("2. Export it: export OPENAI_API_KEY=your_key_here")
    print("3. Pass it when running: OPENAI_API_KEY=your_key_here python run_rag_pdf.py")
    sys.exit(1)
else:
    openai.api_key = os.environ["OPENAI_API_KEY"]
    print("✓ OpenAI API key loaded from environment")

# Create vector database
print("Building vector database...")
vector_db = VectorDatabase()
vector_db = asyncio.run(vector_db.abuild_from_list(split_documents))
print("✓ Vector database built successfully!")

# Test semantic search
print("\nTesting semantic search...")
test_query = "What are the main topics discussed in this document?"
results = vector_db.search_by_text(test_query, k=3)
print(f"\nQuery: {test_query}")
print(f"Found {len(results)} relevant results")

# Task 4 & 5: RAG Pipeline
print("\n\nTask 4 & 5: Setting up RAG pipeline...")

from aimakerspace.openai_utils.prompts import (
    UserRolePrompt,
    SystemRolePrompt,
)
from aimakerspace.openai_utils.chatmodel import ChatOpenAI

# Initialize chat model
chat_openai = ChatOpenAI()

# Define prompts
RAG_SYSTEM_TEMPLATE = """You are a knowledgeable assistant that answers questions based strictly on provided context.

Instructions:
- Only answer questions using information from the provided context
- If the context doesn't contain relevant information, respond with "I don't know"
- Be accurate and cite specific parts of the context when possible
- Keep responses concise and clear
- Only use the provided context. Do not use external knowledge."""

RAG_USER_TEMPLATE = """Context Information:
{context}

Question: {user_query}

Please provide your answer based solely on the context above."""

# Create RAG pipeline class
class SimpleRAGPipeline:
    def __init__(self, llm, vector_db):
        self.llm = llm
        self.vector_db = vector_db
        
    def query(self, question: str, k: int = 3) -> str:
        # Retrieve relevant contexts
        context_list = self.vector_db.search_by_text(question, k=k)
        
        # Format context
        context_prompt = ""
        for i, (context, score) in enumerate(context_list, 1):
            context_prompt += f"[Source {i} - Relevance: {score:.3f}]: {context}\n\n"
        
        # Create messages
        system_prompt = SystemRolePrompt(RAG_SYSTEM_TEMPLATE)
        user_prompt = UserRolePrompt(RAG_USER_TEMPLATE)
        
        messages = [
            system_prompt.create_message(),
            user_prompt.create_message(
                context=context_prompt.strip(),
                user_query=question
            )
        ]
        
        # Get response
        return self.llm.run(messages)

# Create pipeline
rag_pipeline = SimpleRAGPipeline(chat_openai, vector_db)

# Test with example queries
print("\nRAG Pipeline ready! Testing with example queries...\n")

# Different queries based on document type
if data_path.lower().endswith('.pdf'):
    example_queries = [
        "What is the main topic of this PDF document?",
        "Can you summarize the key points from the document?",
        "What are the most important findings or conclusions?"
    ]
else:
    example_queries = [
        "What is the Michael Eisner Memorial Weak Executive Problem?",
        "What advice does Marc give about hiring executives?",
        "What are the key points about startups mentioned in the guide?"
    ]

# Only run first 2 queries to save time
for i, question in enumerate(example_queries[:2], 1):
    print(f"Question {i}: {question}")
    print("\nSearching for relevant context and generating response...")
    response = rag_pipeline.query(question)
    print(f"\nAnswer: {response}\n")
    print("-" * 80)

print("\n✅ PDF support successfully added to the RAG system!")
print("\nUsage examples:")
print("  python run_rag_pdf.py data/PMarcaBlogs.txt  # Process text file")
print("  python run_rag_pdf.py data/example.pdf      # Process PDF file")
print("  python run_rag_pdf.py data/                  # Process all files in directory")
print("\nFor interactive mode in a terminal:")
print("  python run_rag_pdf.py <file> --interactive")