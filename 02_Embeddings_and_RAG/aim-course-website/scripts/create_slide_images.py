#!/usr/bin/env python3
"""
Create slide images for the visual walkthrough
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create output directory
os.makedirs("../static/images", exist_ok=True)

# Slide configurations
slides = [
    {
        "filename": "slide1_document_processing.png",
        "title": "Document Processing Pipeline",
        "content": [
            "1. Load documents (Text & PDF)",
            "2. Split into chunks (1000 chars)",
            "3. Generate embeddings",
            "4. Store in vector database"
        ],
        "color": "#2563eb"
    },
    {
        "filename": "slide2_vector_database.png",
        "title": "Enhanced Vector Database",
        "content": [
            "• Vectors + Rich Metadata",
            "• Source attribution",
            "• Timestamp tracking",
            "• Advanced filtering"
        ],
        "color": "#7c3aed"
    },
    {
        "filename": "slide3_distance_metrics.png",
        "title": "Multiple Distance Metrics",
        "content": [
            "✓ Cosine Similarity",
            "✓ Euclidean Distance",
            "✓ Manhattan Distance",
            "✓ Dot Product",
            "✓ 4 more metrics..."
        ],
        "color": "#10b981"
    },
    {
        "filename": "slide4_rag_pipeline.png",
        "title": "Complete RAG Pipeline",
        "content": [
            "Query → Embed → Search → Retrieve",
            "↓",
            "Generate Response with Citations",
            "[1] Source: paper.pdf, Page 5"
        ],
        "color": "#f59e0b"
    }
]

# Create slides
for slide in slides:
    # Create image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw header
    draw.rectangle([0, 0, 800, 100], fill=slide["color"])
    
    # Try to use a nice font, fall back to default if not available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        content_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        title_font = ImageFont.load_default()
        content_font = ImageFont.load_default()
    
    # Draw title
    draw.text((400, 50), slide["title"], fill='white', font=title_font, anchor="mm")
    
    # Draw content
    y_position = 150
    for line in slide["content"]:
        draw.text((50, y_position), line, fill='#1f2937', font=content_font)
        y_position += 50
    
    # Draw a simple diagram/illustration
    if "document" in slide["filename"]:
        # Document flow
        boxes = [(100, 350), (250, 350), (400, 350), (550, 350)]
        for i, (x, y) in enumerate(boxes):
            draw.rectangle([x, y, x+100, y+80], outline=slide["color"], width=3)
            if i < len(boxes) - 1:
                draw.line([x+100, y+40, boxes[i+1][0], y+40], fill=slide["color"], width=3)
    
    elif "vector" in slide["filename"]:
        # Database illustration
        draw.rectangle([300, 350, 500, 500], outline=slide["color"], width=3)
        for i in range(3):
            y = 370 + i * 40
            draw.line([320, y, 480, y], fill='#e5e7eb', width=2)
    
    elif "metrics" in slide["filename"]:
        # Metrics comparison bars
        metrics = [0.94, 0.89, 0.85, 0.93, 0.91]
        for i, value in enumerate(metrics):
            x = 150 + i * 100
            height = int(value * 150)
            draw.rectangle([x, 500-height, x+60, 500], fill=slide["color"])
    
    elif "pipeline" in slide["filename"]:
        # Pipeline flow
        draw.ellipse([100, 400, 180, 480], outline=slide["color"], width=3)
        draw.line([180, 440, 250, 440], fill=slide["color"], width=3)
        draw.rectangle([250, 400, 350, 480], outline=slide["color"], width=3)
        draw.line([350, 440, 420, 440], fill=slide["color"], width=3)
        draw.rectangle([420, 400, 520, 480], outline=slide["color"], width=3)
        draw.line([520, 440, 590, 440], fill=slide["color"], width=3)
        draw.ellipse([590, 400, 670, 480], outline=slide["color"], width=3)
    
    # Save image
    img.save(f"../static/images/{slide['filename']}")
    print(f"✓ Created {slide['filename']}")

print("\n✅ All slide images created successfully!")