#!/usr/bin/env python3
"""
DrugTox-AI Dashboard - Backend Entry Point
==========================================

Main entry point for the Flask backend application.
"""

import os
import sys
from app import app, predictor

if __name__ == '__main__':
    try:
        # Get the port from environment or command line args, default to 8080
        import sys
        if len(sys.argv) > 1:
            port = int(sys.argv[1])
        else:
            port = int(os.environ.get('PORT', 8080))

        # Show startup banner
        print("🧬 DrugTox-AI Enhanced Dashboard")
        print("=" * 40)
        print(f"📊 Dashboard: http://localhost:{port}")
        print(f"🔬 Prediction API: http://localhost:{port}/api/predict")
        print(f"📈 Statistics: http://localhost:{port}/api/stats")
        print(f"🎯 Endpoints loaded: {len(predictor.endpoints)}")
        print(f"🤖 Model status: {'Active' if predictor.is_loaded else 'Mock Mode'}")
        print("=" * 40)
        print("Starting server... Press Ctrl+C to stop")
        print()

        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("Please check if port 5000 is already in use or try a different port.")
        input("Press Enter to exit...")
    finally:
        print("👋 DrugTox-AI Dashboard shut down")