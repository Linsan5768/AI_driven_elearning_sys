# Backend Server Startup Guide

## ⚠️ Important: Always use virtual environment

The backend server **MUST** be started with the virtual environment activated to ensure all dependencies (including ReportLab) are available.

## Method 1: Use the startup script (Recommended)

```bash
cd backend
./start_server.sh
```

This script will:
- Automatically activate the virtual environment
- Check and install ReportLab if needed
- Start the server with the correct Python

## Method 2: Manual activation

```bash
cd backend
source venv/bin/activate
python3 app.py
```

## Verify correct startup

When the server starts correctly, you should see:

```
🐍 Python executable: /Users/.../backend/venv/bin/python3
🐍 Python version: 3.9.x
✅ ReportLab available: 4.2.5
Starting game server on port 8001...
```

❌ **If you see:**
```
🐍 Python executable: /Applications/Xcode.app/.../python3
❌ ReportLab NOT available
```

**This means you're using system Python. Stop the server and use Method 1 or 2 above.**

