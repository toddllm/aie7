// AIM Course Website JavaScript

// Lambda API endpoint (update this with your actual endpoint)
const API_ENDPOINT = 'https://i074bcdyb2.execute-api.us-east-1.amazonaws.com/';

// Sample queries for demo
const sampleQueries = [
    "What is the Michael Eisner Memorial Weak Executive Problem?",
    "What are the main components of a RAG system?",
    "What advice does Marc Andreessen give about hiring executives?",
    "How do RAG systems combine retrieval and generation?",
    "What are the different distance metrics for vector similarity?"
];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadSampleQueries();
    setupMetricsChart();
    
    // Allow pressing Enter to submit query
    document.getElementById('query-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            submitQuery();
        }
    });
});

// Load sample queries
function loadSampleQueries() {
    const container = document.getElementById('sample-queries');
    sampleQueries.forEach(query => {
        const div = document.createElement('div');
        div.className = 'sample-query';
        div.textContent = query;
        div.onclick = () => {
            document.getElementById('query-input').value = query;
            submitQuery();
        };
        container.appendChild(div);
    });
}

// Submit query to RAG system
async function submitQuery() {
    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();
    
    if (!query) {
        alert('Please enter a question!');
        return;
    }
    
    // Show loading state
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    try {
        // For demo purposes, simulate API call with local data
        // In production, this would call the Lambda function
        await simulateRAGQuery(query);
        
        /* Production code:
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'query',
                query: query,
                k: 3
            })
        });
        
        const data = await response.json();
        displayResults(data);
        */
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error processing query. Please try again.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Simulate RAG query for demo
async function simulateRAGQuery(query) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Generate mock response based on query
    let response, sources;
    
    if (query.toLowerCase().includes('michael eisner')) {
        response = "The Michael Eisner Memorial Weak Executive Problem refers to a tendency where CEOs or startup founders hire weak executives in their own area of expertise to maintain control [1]. This phenomenon is named after Michael Eisner, former CEO of Disney, who struggled to effectively manage ABC after acquiring it despite his TV network expertise [1]. The problem occurs when leaders have difficulty letting go of the function that brought them success, resulting in hiring someone less capable so they can continue to be 'the man' in that area [1].";
        sources = [
            { text: "CEOs hiring weak executives in their area of expertise to maintain control", score: 0.94, metadata: { source: "PMarcaBlogs.txt", author: "Marc Andreessen", chunk_id: 45 } },
            { text: "Michael Eisner's struggle with ABC management despite TV expertise", score: 0.87, metadata: { source: "PMarcaBlogs.txt", author: "Marc Andreessen", chunk_id: 46 } },
            { text: "Leaders difficulty letting go of their original function", score: 0.82, metadata: { source: "PMarcaBlogs.txt", author: "Marc Andreessen", chunk_id: 47 } }
        ];
    } else if (query.toLowerCase().includes('rag') && query.toLowerCase().includes('component')) {
        response = "A RAG (Retrieval-Augmented Generation) system consists of several key components [1][2]: First, the retrieval component that searches for relevant information from external databases [1]. Second, the generation component that processes and creates responses based on retrieved information [2]. Third, the augmentation techniques that enhance retrieval and generation capabilities [2]. These components work together through indexing, embedding, vector storage, semantic search, and response generation with language models [3].";
        sources = [
            { text: "RAG components: retrieval, generation, and augmentation mechanisms", score: 0.92, metadata: { source: "rag_survey_paper.pdf", author: "Gao et al.", page: 5, chunk_id: 12 } },
            { text: "Indexing, embedding, and vector storage for document processing", score: 0.88, metadata: { source: "rag_survey_paper.pdf", author: "Gao et al.", page: 7, chunk_id: 18 } },
            { text: "Semantic search and LLM integration for response generation", score: 0.85, metadata: { source: "rag_survey_paper.pdf", author: "Gao et al.", page: 9, chunk_id: 24 } }
        ];
    } else {
        response = "Based on the documents in our system, here's what I found relevant to your query: RAG systems are designed to enhance language model capabilities by retrieving relevant information from external sources [1]. This approach combines the strengths of retrieval-based and generation-based methods [2]. The key advantage is providing accurate, up-to-date information while maintaining the fluency of language models [3].";
        sources = [
            { text: "RAG enhances LLMs by retrieving relevant external information", score: 0.78, metadata: { source: "rag_survey_paper.pdf", author: "Gao et al.", page: 1, chunk_id: 1 } },
            { text: "Combination of retrieval and generation methods", score: 0.75, metadata: { source: "rag_survey_paper.pdf", author: "Gao et al.", page: 2, chunk_id: 3 } },
            { text: "Providing accurate, up-to-date information with fluent generation", score: 0.72, metadata: { source: "rag_survey_paper.pdf", author: "Gao et al.", page: 3, chunk_id: 5 } }
        ];
    }
    
    displayResults({
        response: response,
        sources: sources,
        query: query
    });
}

// Display query results
function displayResults(data) {
    // Show results section
    document.getElementById('results').style.display = 'block';
    
    // Display response
    document.getElementById('response-text').innerHTML = data.response;
    
    // Display sources
    const sourcesContainer = document.getElementById('sources-list');
    sourcesContainer.innerHTML = '';
    
    data.sources.forEach((source, index) => {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'source-item';
        
        const textDiv = document.createElement('div');
        textDiv.innerHTML = `
            <strong>[${index + 1}]</strong> ${source.text}<br>
            <small style="color: #6b7280;">
                Source: ${source.metadata.source} | 
                Author: ${source.metadata.author} 
                ${source.metadata.page ? `| Page: ${source.metadata.page}` : ''} |
                Chunk: ${source.metadata.chunk_id}
            </small>
        `;
        
        const scoreDiv = document.createElement('div');
        scoreDiv.className = 'source-score';
        scoreDiv.textContent = `${(source.score * 100).toFixed(1)}%`;
        
        sourceDiv.appendChild(textDiv);
        sourceDiv.appendChild(scoreDiv);
        sourcesContainer.appendChild(sourceDiv);
    });
}

// Setup metrics comparison chart
function setupMetricsChart() {
    const ctx = document.getElementById('metricsChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Cosine', 'Euclidean', 'Manhattan', 'Dot Product', 'Correlation'],
            datasets: [{
                label: 'Similarity Score',
                data: [0.94, 0.89, 0.85, 0.93, 0.91],
                backgroundColor: [
                    'rgba(37, 99, 235, 0.8)',
                    'rgba(124, 58, 237, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Distance Metric Comparison on Same Query'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });
}

// Slideshow functionality
let currentSlide = 1;
const totalSlides = 4;

function showSlide(n) {
    const slides = document.getElementsByClassName('slide');
    if (n > totalSlides) currentSlide = 1;
    if (n < 1) currentSlide = totalSlides;
    
    for (let i = 0; i < slides.length; i++) {
        slides[i].classList.remove('active');
    }
    
    slides[currentSlide - 1].classList.add('active');
    document.getElementById('slide-indicator').textContent = `${currentSlide} / ${totalSlides}`;
}

function nextSlide() {
    currentSlide++;
    showSlide(currentSlide);
}

function previousSlide() {
    currentSlide--;
    showSlide(currentSlide);
}

// Initialize slideshow
showSlide(currentSlide);