#!/usr/bin/env python3
"""
Simple DrugTox-AI Server Starter
================================
"""

import os
import sys
import time
import webbrowser
from threading import Timer

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, predictor

def open_browser():
    """Open browser after a delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:8080')

if __name__ == '__main__':
    print("🧬 DrugTox-AI Enhanced Dashboard")
    print("=" * 40)
    print("📊 Dashboard: http://localhost:8080")
    print("🔬 Prediction API: http://localhost:8080/api/predict")
    print("📈 Statistics: http://localhost:8080/api/stats")
    print(f"🎯 Endpoints loaded: {len(predictor.endpoints)}")
    print(f"🤖 Model status: {'Active' if predictor.is_loaded else 'Mock Mode'}")
    print("=" * 40)
    print("🚀 Starting server on port 8080...")
    print("📱 Browser will open automatically")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    # Open browser after delay
    Timer(2.0, open_browser).start()
    
    try:
        app.run(
            host='127.0.0.1',  # Use localhost instead of 0.0.0.0
            port=8080,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
    finally:
        print("👋 DrugTox-AI Dashboard shut down")