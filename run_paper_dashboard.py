"""Unified runner for AtriaTrade Paper Engine & Web Dashboard."""
import sys
import os
import uvicorn

# تنظیم مسیر روت پروژه
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.web.app import app

def main():
    print("=" * 60)
    print("🚀 Starting AtriaTrade Pro (Paper Trading Mode)")
    print("🔒 Mode: 100% Simulated / Paper Trading (No Real Capital)")
    print("🌐 Dashboard URL: http://127.0.0.1:8080")
    print("=" * 60)
    
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
