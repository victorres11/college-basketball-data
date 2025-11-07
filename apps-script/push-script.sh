#!/bin/bash
# Script to push Google Apps Script changes
# Usage: ./push-script.sh (run from project root)

cd "$(dirname "$0")" || exit

# Copy the main script file to Code.gs (clasp expects Code.gs)
cp google-apps-script-cbbd.js Code.gs

# Push to Google Apps Script
clasp push

echo "✅ Script pushed to Google Apps Script successfully!"
echo "📝 Note: All spreadsheets using this library will get the update automatically"

