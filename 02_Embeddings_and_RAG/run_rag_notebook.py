#!/usr/bin/env python3
"""
Command-line runner for the Pythonic RAG Assignment notebook.
This script allows you to execute the notebook step by step from the command line.
"""

import os
import sys
from typing import List, Tuple
import numpy as np
from getpass import getpass

# Task 1: Imports and Utilities
print("Task 1: Setting up imports and utilities...")
from aimakerspace.text_utils import TextFileLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
import asyncio

import nest_asyncio
nest_asyncio.apply()

# Task 2: Documents
print("\nTask 2: Loading and processing documents...")
text_loader = TextFileLoader("data/PMarcaBlogs.txt")
documents = text_loader.load_documents()
print(f"Loaded {len(documents)} document(s)")

# Split documents
text_splitter = CharacterTextSplitter()
split_documents = text_splitter.split_texts(documents)
print(f"Split into {len(split_documents)} chunks")

# Show sample
print("\nFirst document chunk preview:")
print(split_documents[0][:200] + "...")

# Task 3: Embeddings and Vectors
print("\nTask 3: Setting up embeddings and vector database...")

# Get OpenAI API Key
import openai
from dotenv import load_dotenv

# Try to load from .env file
load_dotenv()

if "OPENAI_API_KEY" not in os.environ:
    print("\n⚠️  OpenAI API Key not found!")
    print("Please set your OpenAI API key in one of the following ways:")
    print("1. Create a .env file with: OPENAI_API_KEY=your_key_here")
    print("2. Export it: export OPENAI_API_KEY=your_key_here")
    print("3. Pass it when running: OPENAI_API_KEY=your_key_here python run_rag_notebook.py")
    sys.exit(1)
else:
    openai.api_key = os.environ["OPENAI_API_KEY"]
    print("✓ OpenAI API key loaded from environment")

# Create vector database
print("Building vector database...")
vector_db = VectorDatabase()
vector_db = asyncio.run(vector_db.abuild_from_list(split_documents))
print("Vector database built successfully!")

# Test semantic search
print("\nTesting semantic search...")
query = "What is the Michael Eisner Memorial Weak Executive Problem?"
results = vector_db.search_by_text(query, k=3)
print(f"\nQuery: {query}")
print(f"Found {len(results)} relevant results")
for i, (text, score) in enumerate(results):
    print(f"\nResult {i+1} (score: {score:.4f}):")
    print(text[:200] + "...")

# Task 4 & 5: RAG Pipeline
print("\n\nTask 4 & 5: Setting up RAG pipeline...")

from aimakerspace.openai_utils.prompts import (
    UserRolePrompt,
    SystemRolePrompt,
    AssistantRolePrompt,
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
            context_prompt += f"[Source {i}]: {context}\n\n"
        
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

example_queries = [
    "What is the Michael Eisner Memorial Weak Executive Problem?",
    "What advice does Marc give about hiring executives?",
    "What are the key points about startups mentioned in the guide?"
]

for i, question in enumerate(example_queries, 1):
    print(f"Question {i}: {question}")
    print("\nSearching for relevant context and generating response...")
    response = rag_pipeline.query(question)
    print(f"\nAnswer: {response}\n")
    print("-" * 80)
    
# For interactive mode, you can run this script in a terminal with:
# python run_rag_notebook.py --interactive
if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
    print("\nEntering interactive mode. Type 'exit' to quit.\n")
    while True:
        try:
            question = input("Your question: ")
            if question.lower() == 'exit':
                break
            
            print("\nSearching for relevant context and generating response...")
            response = rag_pipeline.query(question)
            print(f"\nAnswer: {response}\n")
            print("-" * 80)
        except EOFError:
            break

print("\nThank you for using the RAG system!")