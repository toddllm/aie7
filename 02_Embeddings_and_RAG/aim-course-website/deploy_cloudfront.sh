#!/bin/bash

# AWS Deployment Script for AIM Course Website with CloudFront
# This script creates AWS resources with CloudFront HTTPS distribution

echo "🚀 Deploying AIM Course Website with CloudFront HTTPS..."

# Configuration
REGION="us-east-1"
LAMBDA_FUNCTION_NAME="aim-course-rag-demo"
SECRET_NAME="aim-course/openai"
S3_BUCKET_NAME="aim-course-website-$(date +%s)"
API_GATEWAY_NAME="aim-course-api"
CLOUDFRONT_COMMENT="AIM Course Assignment Website"

# Generate cache busting hash based on content
CACHE_BUST_HASH=$(find frontend static -type f -exec md5sum {} \; | md5sum | cut -d' ' -f1 | cut -c1-8)
echo "📝 Cache bust hash: $CACHE_BUST_HASH"

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
pip install -r requirements.txt -t . --quiet
zip -r lambda_deployment.zip . -x "*.pyc" -x "__pycache__/*" > /dev/null
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
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null

aws iam attach-role-policy \
    --role-name aim-course-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite 2>/dev/null

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
        --region $REGION > /dev/null

# Step 5: Create API Gateway
echo "🌐 Step 5: Creating API Gateway..."
API_ID=$(aws apigatewayv2 create-api \
    --name $API_GATEWAY_NAME \
    --protocol-type HTTP \
    --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*" \
    --region $REGION \
    --query 'ApiId' \
    --output text 2>/dev/null || \
    aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='$API_GATEWAY_NAME'].ApiId" --output text | head -1)

# Create Lambda integration
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-uri "arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_FUNCTION_NAME" \
    --payload-format-version 2.0 \
    --region $REGION \
    --query 'IntegrationId' \
    --output text 2>/dev/null || \
    aws apigatewayv2 get-integrations --api-id $API_ID --region $REGION --query 'Items[0].IntegrationId' --output text)

# Create route
aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key 'POST /' \
    --target "integrations/$INTEGRATION_ID" \
    --region $REGION 2>/dev/null

# Deploy API
aws apigatewayv2 create-deployment \
    --api-id $API_ID \
    --region $REGION > /dev/null

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION_NAME \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*" \
    2>/dev/null

API_ENDPOINT="https://$API_ID.execute-api.$REGION.amazonaws.com/"

# Step 6: Update frontend with API endpoint and cache busting
echo "🔧 Step 6: Updating frontend with API endpoint and cache busting..."

# Update API endpoint
sed -i.bak "s|https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod|$API_ENDPOINT|g" static/js/main.js

# Add cache busting to HTML
sed -i.bak "s|style\.css|style.css?v=$CACHE_BUST_HASH|g" frontend/index.html
sed -i.bak "s|main\.js|main.js?v=$CACHE_BUST_HASH|g" frontend/index.html
sed -i.bak "s|assignment2_walkthrough\.mp3|assignment2_walkthrough.mp3?v=$CACHE_BUST_HASH|g" frontend/index.html

# Step 7: Generate TTS audio
echo "🎤 Step 7: Generating TTS audio walkthrough..."
cd scripts
python generate_tts_walkthrough.py
cd ..

# Step 8: Create S3 bucket for static website
echo "☁️ Step 8: Creating S3 bucket..."
aws s3 mb s3://$S3_BUCKET_NAME --region $REGION

# Remove public access block (needed for CloudFront)
aws s3api put-public-access-block \
    --bucket $S3_BUCKET_NAME \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Create CloudFront Origin Access Identity
echo "🔒 Creating CloudFront Origin Access Identity..."
OAI_ID=$(aws cloudfront create-cloud-front-origin-access-identity \
    --cloud-front-origin-access-identity-config \
    CallerReference="aim-course-oai-$(date +%s)",Comment="OAI for AIM Course Website" \
    --query 'CloudFrontOriginAccessIdentity.Id' \
    --output text 2>/dev/null || \
    aws cloudfront list-cloud-front-origin-access-identities \
    --query 'CloudFrontOriginAccessIdentityList.Items[0].Id' \
    --output text)

# Get OAI S3 canonical user ID
OAI_S3_ID=$(aws cloudfront get-cloud-front-origin-access-identity \
    --id $OAI_ID \
    --query 'CloudFrontOriginAccessIdentity.S3CanonicalUserId' \
    --output text)

# Create S3 bucket policy for CloudFront access only
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity $OAI_ID"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $S3_BUCKET_NAME --policy file://bucket-policy.json

# Step 9: Upload website files with cache headers
echo "📤 Step 9: Uploading website files with cache control..."

# HTML files - no cache
aws s3 sync frontend/ s3://$S3_BUCKET_NAME/ \
    --exclude "*.bak" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

# CSS files - cache with revalidation
aws s3 sync static/css/ s3://$S3_BUCKET_NAME/static/css/ \
    --cache-control "public, must-revalidate, max-age=3600" \
    --content-type "text/css"

# JS files - cache with revalidation
aws s3 sync static/js/ s3://$S3_BUCKET_NAME/static/js/ \
    --exclude "*.bak" \
    --cache-control "public, must-revalidate, max-age=3600" \
    --content-type "application/javascript"

# Images - long cache
aws s3 sync static/images/ s3://$S3_BUCKET_NAME/static/images/ \
    --cache-control "public, max-age=86400" \
    --content-type "image/png"

# Audio - long cache
aws s3 sync static/audio/ s3://$S3_BUCKET_NAME/static/audio/ \
    --cache-control "public, max-age=86400" \
    --content-type "audio/mpeg"

# Step 10: Create CloudFront distribution
echo "☁️ Step 10: Creating CloudFront distribution..."

# Create distribution configuration
cat > cloudfront-config.json << EOF
{
    "CallerReference": "aim-course-$(date +%s)",
    "Comment": "$CLOUDFRONT_COMMENT",
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-$S3_BUCKET_NAME",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"]
        },
        "ForwardedValues": {
            "QueryString": true,
            "Cookies": {"Forward": "none"},
            "Headers": {
                "Quantity": 0
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "MinTTL": 0,
        "DefaultTTL": 3600,
        "MaxTTL": 86400,
        "Compress": true
    },
    "CacheBehaviors": {
        "Quantity": 1,
        "Items": [{
            "PathPattern": "*.html",
            "TargetOriginId": "S3-$S3_BUCKET_NAME",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            },
            "ForwardedValues": {
                "QueryString": false,
                "Cookies": {"Forward": "none"}
            },
            "TrustedSigners": {
                "Enabled": false,
                "Quantity": 0
            },
            "MinTTL": 0,
            "DefaultTTL": 0,
            "MaxTTL": 0,
            "Compress": true
        }]
    },
    "Origins": {
        "Quantity": 1,
        "Items": [{
            "Id": "S3-$S3_BUCKET_NAME",
            "DomainName": "$S3_BUCKET_NAME.s3.amazonaws.com",
            "S3OriginConfig": {
                "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
            }
        }]
    },
    "DefaultRootObject": "index.html",
    "Enabled": true,
    "PriceClass": "PriceClass_100",
    "ViewerCertificate": {
        "CloudFrontDefaultCertificate": true
    }
}
EOF

# Create distribution
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text)

DISTRIBUTION_DOMAIN=$(aws cloudfront get-distribution \
    --id $DISTRIBUTION_ID \
    --query 'Distribution.DomainName' \
    --output text)

echo "⏳ Waiting for CloudFront distribution to deploy (this may take 5-10 minutes)..."

# Wait for distribution to be deployed
while true; do
    STATUS=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.Status' --output text)
    if [ "$STATUS" = "Deployed" ]; then
        break
    fi
    echo -n "."
    sleep 30
done
echo " Deployed!"

# Step 11: Create cache invalidation
echo "🔄 Step 11: Creating cache invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ Cache invalidation created: $INVALIDATION_ID"

# Clean up temporary files
rm -f trust-policy.json bucket-policy.json cloudfront-config.json backend/lambda_deployment.zip *.bak frontend/*.bak static/js/*.bak

echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Summary:"
echo "===================="
echo "🌐 CloudFront URL: https://$DISTRIBUTION_DOMAIN"
echo "☁️ Distribution ID: $DISTRIBUTION_ID"
echo "🔌 API Endpoint: $API_ENDPOINT"
echo "⚡ Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "🔐 Secret Name: $SECRET_NAME"
echo "☁️ S3 Bucket: $S3_BUCKET_NAME"
echo "🔄 Cache Bust Hash: $CACHE_BUST_HASH"
echo ""
echo "🎉 Your AIM Course website is now live with HTTPS!"
echo "Visit https://$DISTRIBUTION_DOMAIN to see your assignment portfolio."
echo ""
echo "📝 Note: CloudFront may take 5-10 minutes to fully propagate globally."
echo "To update content, run this script again - it will automatically invalidate the cache."

# Save deployment info
cat > deployment-info.json << EOF
{
  "cloudfront_url": "https://$DISTRIBUTION_DOMAIN",
  "distribution_id": "$DISTRIBUTION_ID",
  "s3_bucket": "$S3_BUCKET_NAME",
  "api_endpoint": "$API_ENDPOINT",
  "lambda_function": "$LAMBDA_FUNCTION_NAME",
  "cache_bust_hash": "$CACHE_BUST_HASH",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo ""
echo "📄 Deployment info saved to deployment-info.json"