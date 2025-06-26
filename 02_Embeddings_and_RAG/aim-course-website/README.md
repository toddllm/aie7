# AIM Course Website

A comprehensive portfolio website for AI Maker Space course assignments, featuring interactive demos and detailed explanations.

## 🌟 Features

- **Interactive RAG Demo**: Live demonstration of the enhanced RAG system
- **Audio Walkthrough**: 2-minute TTS-generated explanation of the assignment
- **Visual Slides**: Step-by-step breakdown of key implementations
- **Q&A Section**: Answers to all assignment questions
- **AWS Lambda Backend**: Serverless API for RAG queries
- **Responsive Design**: Works on all devices

## 🏗️ Architecture

```
Frontend (S3 Static Website)
    ↓
API Gateway
    ↓
Lambda Function
    ↓
AWS Secrets Manager (OpenAI Key)
```

## 🚀 Deployment

### Prerequisites
- AWS CLI configured with appropriate credentials
- Python 3.9+
- OpenAI API key in `.env` file
- jq (for JSON processing in update script)

### Deploy with CloudFront HTTPS
```bash
./deploy_cloudfront.sh
```

This enhanced script will:
1. Create AWS Secret for OpenAI API key
2. Deploy Lambda function with RAG logic
3. Set up API Gateway with CORS
4. Create S3 bucket with CloudFront-only access
5. Generate TTS audio walkthrough
6. Create CloudFront distribution with HTTPS
7. Implement aggressive cache busting
8. Invalidate CloudFront cache on deploy

### Update Content
```bash
./update_content.sh
```

This script:
- Updates cache bust hashes
- Syncs new content to S3
- Creates CloudFront invalidation
- Ensures all users see latest version

### Original S3-only Deploy (HTTP)
```bash
./deploy.sh  # Original script for S3 static hosting
```

## 📁 Project Structure

```
aim-course-website/
├── frontend/          # HTML files
├── static/           
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript
│   ├── audio/        # TTS walkthrough
│   └── images/       # Slide images
├── backend/          # Lambda function
├── scripts/          # Utility scripts
└── deploy.sh         # Deployment script
```

## 🔧 Local Development

### Run locally:
```bash
# Start a local server
cd frontend
python -m http.server 8000
```

### Update Lambda function:
```bash
cd backend
zip -r lambda_deployment.zip . -x "*.pyc"
aws lambda update-function-code --function-name aim-course-rag-demo --zip-file fileb://lambda_deployment.zip
```

## 📊 Assignment Highlights

### Three Major Enhancements:
1. **PDF Support**: Universal document loader for multiple formats
2. **Distance Metrics**: 8 different similarity measures
3. **Metadata Support**: Rich filtering and source attribution

### Key Achievements:
- Processed 27-page academic papers
- Implemented production-ready features
- Created comprehensive documentation
- Built interactive demonstrations

## 🎯 Future Assignments

This website structure supports adding future assignments:
- Create new subdirectories for each assignment
- Update navigation to include new sections
- Reuse Lambda infrastructure for demos

## 📝 Notes

- The Lambda function uses mock data for the demo
- In production, integrate with a real vector database
- Consider adding authentication for private assignments
- CloudFront can be added for better performance

## 🤝 Contributing

To add new assignments:
1. Create assignment directory
2. Follow existing HTML structure
3. Update navigation links
4. Deploy with updated content

## 📄 License

This project is part of the AI Maker Space course curriculum.

## 👨‍💻 Author

Todd (ToddLLM) Deshane, Ph.D. - 2025