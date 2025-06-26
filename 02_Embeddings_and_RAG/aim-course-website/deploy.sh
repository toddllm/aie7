#!/bin/bash

# AWS Deployment Script for AIM Course Website
# This script creates the necessary AWS resources and deploys the website

echo "🚀 Deploying AIM Course Website..."

# Configuration
REGION="us-east-1"
LAMBDA_FUNCTION_NAME="aim-course-rag-demo"
SECRET_NAME="aim-course/openai"
S3_BUCKET_NAME="aim-course-website-$(date +%s)"
API_GATEWAY_NAME="aim-course-api"

# Step 1: Create AWS Secret for OpenAI API Key
echo "📝 Step 1: Creating AWS Secret..."
if [ -f "../.env" ]; then
    OPENAI_KEY=$(grep OPENAI_API_KEY ../.env | cut -d '=' -f2)
    aws secretsmanager create-secret \
        --name $SECRET_NAME \
        --region $REGION \
        --secret-string "{\"api_key\":\"$OPENAI_KEY\"}" \
        2>/dev/null || echo "Secret already exists"
else
    echo "❌ Error: ../.env file not found. Please ensure OPENAI_API_KEY is set."
    exit 1
fi

# Step 2: Create Lambda deployment package
echo "📦 Step 2: Creating Lambda deployment package..."
cd backend
pip install -r requirements.txt -t .
zip -r lambda_deployment.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

# Step 3: Create IAM role for Lambda
echo "🔐 Step 3: Creating IAM role..."
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

ROLE_ARN=$(aws iam create-role \
    --role-name aim-course-lambda-role \
    --assume-role-policy-document file://trust-policy.json \
    --query 'Role.Arn' \
    --output text 2>/dev/null || \
    aws iam get-role --role-name aim-course-lambda-role --query 'Role.Arn' --output text)

# Attach policies
aws iam attach-role-policy \
    --role-name aim-course-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name aim-course-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

# Wait for role to propagate
sleep 10

# Step 4: Create Lambda function
echo "⚡ Step 4: Creating Lambda function..."
aws lambda create-function \
    --function-name $LAMBDA_FUNCTION_NAME \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://backend/lambda_deployment.zip \
    --timeout 30 \
    --memory-size 512 \
    --region $REGION \
    2>/dev/null || \
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://backend/lambda_deployment.zip \
        --region $REGION

# Step 5: Create API Gateway
echo "🌐 Step 5: Creating API Gateway..."
API_ID=$(aws apigatewayv2 create-api \
    --name $API_GATEWAY_NAME \
    --protocol-type HTTP \
    --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*" \
    --region $REGION \
    --query 'ApiId' \
    --output text 2>/dev/null || \
    aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='$API_GATEWAY_NAME'].ApiId" --output text)

# Create Lambda integration
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-uri "arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_FUNCTION_NAME" \
    --payload-format-version 2.0 \
    --region $REGION \
    --query 'IntegrationId' \
    --output text)

# Create route
aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key 'POST /' \
    --target "integrations/$INTEGRATION_ID" \
    --region $REGION

# Deploy API
aws apigatewayv2 create-deployment \
    --api-id $API_ID \
    --region $REGION

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION_NAME \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*" \
    2>/dev/null

API_ENDPOINT="https://$API_ID.execute-api.$REGION.amazonaws.com/"

# Step 6: Update frontend with API endpoint
echo "🔧 Step 6: Updating frontend with API endpoint..."
sed -i.bak "s|https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod|$API_ENDPOINT|g" static/js/main.js

# Step 7: Generate TTS audio
echo "🎤 Step 7: Generating TTS audio walkthrough..."
cd scripts
python generate_tts_walkthrough.py
cd ..

# Step 8: Create S3 bucket for static website
echo "☁️ Step 8: Creating S3 bucket for website..."
aws s3 mb s3://$S3_BUCKET_NAME --region $REGION

# Configure bucket for static website hosting
aws s3 website s3://$S3_BUCKET_NAME \
    --index-document index.html \
    --error-document error.html

# Set bucket policy for public access
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $S3_BUCKET_NAME --policy file://bucket-policy.json

# Step 9: Upload website files
echo "📤 Step 9: Uploading website files..."
aws s3 sync frontend/ s3://$S3_BUCKET_NAME/ --exclude "*.bak"
aws s3 sync static/ s3://$S3_BUCKET_NAME/static/

# Get website URL
WEBSITE_URL="http://$S3_BUCKET_NAME.s3-website-$REGION.amazonaws.com"

# Clean up temporary files
rm -f trust-policy.json bucket-policy.json backend/lambda_deployment.zip

echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Summary:"
echo "===================="
echo "🌐 Website URL: $WEBSITE_URL"
echo "🔌 API Endpoint: $API_ENDPOINT"
echo "⚡ Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "🔐 Secret Name: $SECRET_NAME"
echo "☁️ S3 Bucket: $S3_BUCKET_NAME"
echo ""
echo "🎉 Your AIM Course website is now live!"
echo "Visit $WEBSITE_URL to see your assignment portfolio."