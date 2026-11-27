#!/bin/bash
cd "$(dirname "$0")"
echo "======================================================"
echo "  🚀 Starting Smart Gmail Spam Classifier Dashboard   "
echo "======================================================"
echo "Opening app in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server when done."
echo ""
if [ -f "./venv/bin/python3" ]; then
    ./venv/bin/python3 -m streamlit run app.py
else
    python3 -m streamlit run app.py
fi
