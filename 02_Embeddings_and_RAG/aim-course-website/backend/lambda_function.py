"""
AWS Lambda function for AIM Course RAG Demo
Handles RAG queries using OpenAI API with key from AWS Secrets Manager
"""

import json
import boto3
import os
from typing import Dict, Any, List
import numpy as np
from base64 import b64decode

# OpenAI imports
import openai

# Get secrets from AWS Secrets Manager
def get_secret(secret_name: str, region_name: str = "us-east-1") -> Dict[str, Any]:
    """Retrieve secret from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e
    
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# Initialize OpenAI with secret
try:
    secrets = get_secret("aim-course/openai")
    openai.api_key = secrets['api_key']
except Exception as e:
    print(f"Error loading secrets: {e}")

# Sample document chunks for demo (in production, these would be in a database)
SAMPLE_CHUNKS = [
    {
        "text": "The Michael Eisner Memorial Weak Executive Problem refers to CEOs hiring weak executives in their area of expertise to maintain control.",
        "metadata": {"source": "PMarcaBlogs.txt", "author": "Marc Andreessen", "chunk_id": 1}
    },
    {
        "text": "RAG systems combine retrieval mechanisms with generation models to provide accurate, context-aware responses.",
        "metadata": {"source": "rag_survey_paper.pdf", "author": "Gao et al.", "page": 3, "chunk_id": 2}
    },
    {
        "text": "When hiring executives, focus on strength rather than lack of weakness. Everyone has severe weaknesses.",
        "metadata": {"source": "PMarcaBlogs.txt", "author": "Marc Andreessen", "chunk_id": 3}
    }
]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    v1_np = np.array(v1)
    v2_np = np.array(v2)
    return np.dot(v1_np, v2_np) / (np.linalg.norm(v1_np) * np.linalg.norm(v2_np))

def get_embedding(text: str) -> List[float]:
    """Get embedding from OpenAI"""
    response = openai.Embedding.create(
        model="text-embedding-3-small",
        input=text
    )
    return response['data'][0]['embedding']

def search_chunks(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Search for relevant chunks using embeddings"""
    query_embedding = get_embedding(query)
    
    # Calculate similarities
    results = []
    for chunk in SAMPLE_CHUNKS:
        chunk_embedding = get_embedding(chunk['text'])
        similarity = cosine_similarity(query_embedding, chunk_embedding)
        results.append({
            "text": chunk['text'],
            "metadata": chunk['metadata'],
            "score": similarity
        })
    
    # Sort by similarity and return top k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:k]

def generate_response(query: str, context: List[Dict[str, Any]]) -> str:
    """Generate response using GPT-4-mini with context"""
    # Format context with citations
    context_text = ""
    for i, item in enumerate(context, 1):
        context_text += f"[{i}] {item['text']}\n"
        context_text += f"    Source: {item['metadata']['source']}, "
        context_text += f"Author: {item['metadata']['author']}\n\n"
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Answer based on the provided context and include source citations."
        },
        {
            "role": "user",
            "content": f"Context:\n{context_text}\nQuestion: {query}\n\nAnswer with citations:"
        }
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def lambda_handler(event, context):
    """Main Lambda handler"""
    # Enable CORS and security headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:;"
    }
    
    # Handle preflight
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Parse request
        body = json.loads(event['body'])
        action = body.get('action', 'query')
        
        if action == 'query':
            query = body.get('query', '')
            k = body.get('k', 3)
            
            # Search for relevant chunks
            search_results = search_chunks(query, k)
            
            # Generate response
            response = generate_response(query, search_results)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'response': response,
                    'sources': search_results,
                    'query': query
                })
            }
            
        elif action == 'get_sample_queries':
            # Return sample queries for the demo
            samples = [
                "What is the Michael Eisner Memorial Weak Executive Problem?",
                "What are the main components of a RAG system?",
                "What advice does Marc Andreessen give about hiring executives?",
                "How do RAG systems combine retrieval and generation?",
                "What are the different distance metrics for vector similarity?"
            ]
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'samples': samples})
            }
            
        else:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid action'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }