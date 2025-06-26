#!/bin/bash

# Update script for existing CloudFront deployment
# This updates content and invalidates the cache

echo "🔄 Updating AIM Course Website Content..."

# Check if deployment info exists
if [ ! -f "deployment-info.json" ]; then
    echo "❌ Error: deployment-info.json not found. Please run deploy_cloudfront.sh first."
    exit 1
fi

# Read deployment info
S3_BUCKET=$(jq -r '.s3_bucket' deployment-info.json)
DISTRIBUTION_ID=$(jq -r '.distribution_id' deployment-info.json)
API_ENDPOINT=$(jq -r '.api_endpoint' deployment-info.json)

echo "📝 Current deployment:"
echo "  S3 Bucket: $S3_BUCKET"
echo "  Distribution ID: $DISTRIBUTION_ID"

# Generate new cache bust hash
CACHE_BUST_HASH=$(find frontend static -type f -exec md5sum {} \; | md5sum | cut -d' ' -f1 | cut -c1-8)
echo "📝 New cache bust hash: $CACHE_BUST_HASH"

# Update cache busting in HTML files
echo "🔧 Updating cache bust parameters..."
cp frontend/index.html frontend/index.html.bak

# Reset to original first
sed -i '' 's/style\.css?v=[a-zA-Z0-9]*/style.css/g' frontend/index.html
sed -i '' 's/main\.js?v=[a-zA-Z0-9]*/main.js/g' frontend/index.html
sed -i '' 's/assignment2_walkthrough\.mp3?v=[a-zA-Z0-9]*/assignment2_walkthrough.mp3/g' frontend/index.html

# Apply new cache bust
sed -i '' "s|style\.css|style.css?v=$CACHE_BUST_HASH|g" frontend/index.html
sed -i '' "s|main\.js|main.js?v=$CACHE_BUST_HASH|g" frontend/index.html
sed -i '' "s|assignment2_walkthrough\.mp3|assignment2_walkthrough.mp3?v=$CACHE_BUST_HASH|g" frontend/index.html

# Ensure API endpoint is correct
sed -i '' "s|https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod|$API_ENDPOINT|g" static/js/main.js

# Upload updated files with proper cache headers
echo "📤 Uploading updated files..."

# HTML files - no cache
aws s3 sync frontend/ s3://$S3_BUCKET/ \
    --exclude "*.bak" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html" \
    --delete

# CSS files - cache with revalidation
aws s3 sync static/css/ s3://$S3_BUCKET/static/css/ \
    --cache-control "public, must-revalidate, max-age=3600" \
    --content-type "text/css" \
    --delete

# JS files - cache with revalidation
aws s3 sync static/js/ s3://$S3_BUCKET/static/js/ \
    --exclude "*.bak" \
    --cache-control "public, must-revalidate, max-age=3600" \
    --content-type "application/javascript" \
    --delete

# Images - long cache
aws s3 sync static/images/ s3://$S3_BUCKET/static/images/ \
    --cache-control "public, max-age=86400" \
    --content-type "image/png" \
    --delete

# Audio - long cache
aws s3 sync static/audio/ s3://$S3_BUCKET/static/audio/ \
    --cache-control "public, max-age=86400" \
    --content-type "audio/mpeg" \
    --delete

# Create CloudFront invalidation
echo "🔄 Creating CloudFront cache invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ Invalidation created: $INVALIDATION_ID"

# Wait for invalidation to complete
echo "⏳ Waiting for invalidation to complete..."
while true; do
    STATUS=$(aws cloudfront get-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --id $INVALIDATION_ID \
        --query 'Invalidation.Status' \
        --output text)
    
    if [ "$STATUS" = "Completed" ]; then
        echo "✅ Invalidation completed!"
        break
    fi
    
    echo -n "."
    sleep 5
done

# Update deployment info
jq --arg hash "$CACHE_BUST_HASH" \
   --arg date "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
   '.cache_bust_hash = $hash | .last_updated = $date' \
   deployment-info.json > deployment-info.json.tmp && \
   mv deployment-info.json.tmp deployment-info.json

# Clean up
rm -f frontend/*.bak static/js/*.bak

echo ""
echo "✅ Update complete!"
echo "🌐 Your changes are now live at: $(jq -r '.cloudfront_url' deployment-info.json)"
echo "🔄 Cache has been invalidated - all users will see the latest version"