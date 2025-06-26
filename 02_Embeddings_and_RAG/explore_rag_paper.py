#!/usr/bin/env python3
"""
Explore the RAG survey paper with specific technical queries
"""

import os
import sys
from dotenv import load_dotenv
import asyncio
import nest_asyncio

# Setup
nest_asyncio.apply()
load_dotenv()

from aimakerspace.pdf_loader import UniversalLoader
from aimakerspace.text_utils import CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.prompts import UserRolePrompt, SystemRolePrompt
from aimakerspace.openai_utils.chatmodel import ChatOpenAI

print("Loading and processing RAG survey paper...")
print("=" * 60)

# Load the paper
loader = UniversalLoader("data/rag_survey_paper.pdf")
documents = loader.load_documents()

# Split into chunks
splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
chunks = splitter.split_texts(documents)
print(f"✓ Loaded paper and split into {len(chunks)} chunks\n")

# Build vector database
print("Building vector database...")
vector_db = VectorDatabase()
vector_db = asyncio.run(vector_db.abuild_from_list(chunks))
print("✓ Vector database ready\n")

# Setup RAG pipeline
chat_openai = ChatOpenAI()

RAG_SYSTEM_TEMPLATE = """You are an expert AI researcher analyzing academic papers. 
Answer questions based strictly on the provided context from the paper.
Be specific and cite relevant sections when possible.
If the context doesn't contain the answer, say so clearly."""

RAG_USER_TEMPLATE = """Context from the paper:
{context}

Question: {user_query}

Please provide a detailed answer based on the context above."""

class AcademicRAGPipeline:
    def __init__(self, llm, vector_db):
        self.llm = llm
        self.vector_db = vector_db
        
    def query(self, question: str, k: int = 5) -> dict:
        # Retrieve more context for academic queries
        context_list = self.vector_db.search_by_text(question, k=k)
        
        # Format context with scores
        context_prompt = ""
        sources = []
        for i, (context, score) in enumerate(context_list, 1):
            context_prompt += f"[Extract {i} - Relevance: {score:.3f}]:\n{context}\n\n"
            sources.append((i, score, context[:100] + "..."))
        
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
        response = self.llm.run(messages)
        
        return {
            "answer": response,
            "sources": sources,
            "num_sources": len(sources)
        }

# Create pipeline
rag_pipeline = AcademicRAGPipeline(chat_openai, vector_db)

# Technical queries about RAG
queries = [
    "What are the main components of a RAG system according to this survey?",
    "What are the different retrieval enhancement methods mentioned in the paper?",
    "How does the paper categorize different RAG paradigms?",
    "What are the evaluation metrics for RAG systems discussed in the paper?",
    "What future research directions for RAG does the paper suggest?"
]

print("Exploring RAG concepts from the survey paper:")
print("=" * 60)

for i, question in enumerate(queries, 1):
    print(f"\n📌 Question {i}: {question}")
    print("-" * 60)
    
    result = rag_pipeline.query(question)
    
    print(f"\n💡 Answer:\n{result['answer']}")
    
    print(f"\n📚 Based on {result['num_sources']} relevant extracts")
    print("Top sources:")
    for idx, score, preview in result['sources'][:3]:
        print(f"  - Extract {idx} (relevance: {score:.3f}): {preview}")
    
    print("\n" + "=" * 60)

print("\n✅ Analysis complete!")