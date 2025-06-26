#!/usr/bin/env python3
"""
Demonstration of enhanced RAG features:
1. Multiple distance metrics
2. Metadata support for filtering and attribution
"""

import os
import sys
import asyncio
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# Setup
load_dotenv()

from aimakerspace.pdf_loader import UniversalLoader
from aimakerspace.text_utils import CharacterTextSplitter
from aimakerspace.enhanced_vectordatabase import EnhancedVectorDatabase
from aimakerspace.distance_metrics import DISTANCE_METRICS
from aimakerspace.openai_utils.prompts import UserRolePrompt, SystemRolePrompt
from aimakerspace.openai_utils.chatmodel import ChatOpenAI

print("Enhanced RAG Features Demonstration")
print("=" * 60)

# Check API key
if "OPENAI_API_KEY" not in os.environ:
    print("Please set OPENAI_API_KEY in .env file")
    sys.exit(1)

# Load multiple documents with different sources
print("\n1. Loading documents with metadata...")
documents_with_metadata = []

# Load text file
text_loader = UniversalLoader("data/PMarcaBlogs.txt")
text_docs = text_loader.load_documents()
print(f"✓ Loaded {len(text_docs)} text document(s)")

# Load PDF file
pdf_loader = UniversalLoader("data/rag_survey_paper.pdf")
pdf_docs = pdf_loader.load_documents()
print(f"✓ Loaded {len(pdf_docs)} PDF document(s)")

# Split documents and add metadata
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# Process text documents
text_chunks = splitter.split_texts(text_docs)
text_metadata = []
for i, chunk in enumerate(text_chunks):
    text_metadata.append({
        "source": "PMarcaBlogs.txt",
        "source_type": "text",
        "chunk_id": i,
        "total_chunks": len(text_chunks),
        "author": "Marc Andreessen",
        "topic": "startups and business"
    })

# Process PDF documents
pdf_chunks = splitter.split_texts(pdf_docs)
pdf_metadata = []
for i, chunk in enumerate(pdf_chunks):
    # Extract page number if available
    page_num = None
    if "--- Page" in chunk:
        try:
            page_start = chunk.find("--- Page") + 9
            page_end = chunk.find("---", page_start)
            page_num = int(chunk[page_start:page_end].strip())
        except:
            pass
    
    pdf_metadata.append({
        "source": "rag_survey_paper.pdf",
        "source_type": "pdf",
        "chunk_id": i,
        "total_chunks": len(pdf_chunks),
        "page": page_num,
        "author": "Gao et al.",
        "topic": "RAG survey",
        "year": 2023
    })

# Combine all chunks and metadata
all_chunks = text_chunks[:50] + pdf_chunks[:50]  # Use subset for demo
all_metadata = text_metadata[:50] + pdf_metadata[:50]

print(f"\nTotal chunks to process: {len(all_chunks)}")

# Test different distance metrics
print("\n2. Testing Different Distance Metrics")
print("=" * 60)

test_query = "What are the best practices for hiring executives?"

for metric_name in ["cosine", "euclidean", "manhattan", "dot_product"]:
    print(f"\nUsing {metric_name} distance:")
    
    # Create vector database with specific metric
    vector_db = EnhancedVectorDatabase(distance_metric=metric_name)
    vector_db = asyncio.run(vector_db.abuild_from_list(all_chunks, all_metadata))
    
    # Search
    results = vector_db.search_by_text(test_query, k=3)
    
    for i, (text, score, metadata) in enumerate(results, 1):
        print(f"  {i}. Score: {score:.4f}")
        print(f"     Source: {metadata['source']} (chunk {metadata['chunk_id']})")
        print(f"     Preview: {text[:100]}...")

# Demonstrate metadata filtering
print("\n\n3. Metadata Filtering Demonstration")
print("=" * 60)

# Create a single database for filtering demos
vector_db = EnhancedVectorDatabase(distance_metric="cosine")
vector_db = asyncio.run(vector_db.abuild_from_list(all_chunks, all_metadata))

# Filter by source type
print("\nFilter: Only PDF documents")
pdf_results = vector_db.search_by_text(
    "What is RAG?",
    k=3,
    metadata_filter={"source_type": "pdf"}
)

for i, (text, score, metadata) in enumerate(pdf_results, 1):
    print(f"  {i}. Source: {metadata['source']} (Page {metadata.get('page', 'N/A')})")
    print(f"     Score: {score:.4f}")

# Filter by topic
print("\n\nFilter: Only startup-related content")
startup_results = vector_db.search_by_text(
    "What advice for founders?",
    k=3,
    metadata_filter={"topic": "startups and business"}
)

for i, (text, score, metadata) in enumerate(startup_results, 1):
    print(f"  {i}. Source: {metadata['source']} (Author: {metadata['author']})")
    print(f"     Score: {score:.4f}")

# Database statistics
print("\n\n4. Database Statistics")
print("=" * 60)
stats = vector_db.get_statistics()
for key, value in stats.items():
    print(f"{key}: {value}")

# Advanced RAG with metadata
print("\n\n5. RAG Pipeline with Metadata Context")
print("=" * 60)

# Create RAG pipeline that includes metadata in context
chat_openai = ChatOpenAI()

RAG_SYSTEM_TEMPLATE = """You are a knowledgeable assistant that answers questions based on provided documents.
When answering, cite the source document and page number (if available) for transparency."""

RAG_USER_TEMPLATE = """Sources and Context:
{context_with_metadata}

Question: {user_query}

Please answer based on the provided sources, citing them appropriately."""

def create_context_with_metadata(results):
    """Format search results with metadata for the prompt."""
    context_parts = []
    for i, (text, score, metadata) in enumerate(results, 1):
        source_info = f"[Source {i}: {metadata['source']}"
        if metadata.get('page'):
            source_info += f", Page {metadata['page']}"
        source_info += f", Author: {metadata.get('author', 'Unknown')}]"
        
        context_parts.append(f"{source_info}\n{text}\n")
    
    return "\n".join(context_parts)

# Query with metadata-aware RAG
query = "What are the main components of a RAG system and what advice exists for startup hiring?"

# Search across both sources
results = vector_db.search_by_text(query, k=4)
context = create_context_with_metadata(results)

system_prompt = SystemRolePrompt(RAG_SYSTEM_TEMPLATE)
user_prompt = UserRolePrompt(RAG_USER_TEMPLATE)

messages = [
    system_prompt.create_message(),
    user_prompt.create_message(
        context_with_metadata=context,
        user_query=query
    )
]

print(f"Query: {query}\n")
response = chat_openai.run(messages)
print(f"Answer:\n{response}")

print("\n\n✅ Enhanced features demonstration complete!")
print("\nKey enhancements demonstrated:")
print("1. Multiple distance metrics (cosine, euclidean, manhattan, dot product)")
print("2. Metadata storage and filtering")
print("3. Source attribution in RAG responses")
print("4. Cross-document querying with proper citations")