#!/usr/bin/env python3
"""
Generate TTS audio walkthrough for Assignment 2: Embeddings and RAG
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if "OPENAI_API_KEY" not in os.environ:
    print("Please set OPENAI_API_KEY in .env file")
    sys.exit(1)

client = OpenAI()

# Audio walkthrough script (2-3 minutes target)
WALKTHROUGH_SCRIPT = """
Welcome to Assignment 2: Embeddings and RAG.

In this assignment, we built a complete Retrieval Augmented Generation system from scratch, then enhanced it with three major improvements.

First, let's understand what we built. Our RAG system has five main components:
1. Document loading and chunking
2. Creating embeddings with OpenAI's text-embedding-3-small model
3. Storing vectors in a vector database
4. Semantic search using cosine similarity
5. Generating responses with GPT-4-mini using retrieved context

Now, let's discuss our three enhancements:

Enhancement 1: PDF Support. We created a Universal Loader that automatically detects and processes both text and PDF files. We tested it with a 27-page academic paper on RAG systems, demonstrating real-world applicability.

Enhancement 2: Multiple Distance Metrics. Beyond cosine similarity, we implemented 8 different distance measures including Euclidean, Manhattan, and dot product. This gives flexibility to optimize retrieval for different use cases.

Enhancement 3: Metadata Support. We built an Enhanced Vector Database that stores rich metadata like source documents, authors, and timestamps. This enables filtered searches and source attribution in responses, making the system more transparent and production-ready.

Key achievements include: Processing complex academic PDFs, comparing retrieval quality across metrics, and providing source citations in all responses.

The system is now versatile enough for real-world applications, handling multiple document formats with full transparency and traceability.

Thank you for reviewing this assignment. The website contains interactive demos and detailed explanations of each enhancement.
"""

# Generate audio
def generate_audio_walkthrough():
    """Generate TTS audio for the walkthrough"""
    print("Generating audio walkthrough...")
    
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # Professional, clear voice
            input=WALKTHROUGH_SCRIPT,
            speed=1.1  # Slightly faster for conciseness
        )
        
        # Save audio file
        audio_path = Path("../static/audio/assignment2_walkthrough.mp3")
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        response.stream_to_file(audio_path)
        print(f"✓ Audio saved to: {audio_path}")
        
        # Calculate approximate duration (rough estimate)
        word_count = len(WALKTHROUGH_SCRIPT.split())
        wpm = 150 * 1.1  # Words per minute with speed adjustment
        duration_minutes = word_count / wpm
        print(f"✓ Estimated duration: {duration_minutes:.1f} minutes")
        
        return str(audio_path)
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

if __name__ == "__main__":
    audio_file = generate_audio_walkthrough()
    if audio_file:
        print("\n✅ Audio walkthrough generated successfully!")
        print("You can now use this in the website's audio player.")