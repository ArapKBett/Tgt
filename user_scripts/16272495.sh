#!/bin/bash
EMAIL="bettarap254@gmail.com"  # CHANGE THIS
URLS=(
    "https://www...."
    # Add more URLs below
)
for URL in "${URLS[@]}"; do
    echo "Submitting legal request for $URL"
    curl -X POST "https://support.google.com/legal/contact/lr_crawler_removal" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "product=websearch&url=$URL&email=$EMAIL&reason=personal_info"
    sleep 2
done