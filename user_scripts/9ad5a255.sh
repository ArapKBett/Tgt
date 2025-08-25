#!/bin/bash

EMAIL="admin@einforma.com"
URLS=(
    "https://www....."
)

for URL in "${URLS[@]}"; do
    curl -X POST "https://www.google.com/webmasters/tools/legal-removal-request" \
    -H "Content-Type: application/json" \
    -d '{
        "complaintType": "RIGHT_TO_BE_FORGOTTEN",
        "affectedUrls": ["'"$URL"'"],
        "contactEmail": "'"$EMAIL"'",
        "reason": "This page exposes my personal data due to a phishing attack."
    }'
    sleep 2
done