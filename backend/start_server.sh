#!/bin/bash

# Start Flask server with virtual environment
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Check if ReportLab is installed
python3 -c "import reportlab" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  ReportLab not found in virtual environment. Installing..."
    pip install reportlab==4.2.5
fi

# Start Flask server
echo "🚀 Starting Flask server with virtual environment..."
echo "📦 Python: $(which python3)"
echo "📚 ReportLab: $(python3 -c 'import reportlab; print(reportlab.__version__)' 2>/dev/null || echo 'Not installed')"
echo ""

python3 app.py

