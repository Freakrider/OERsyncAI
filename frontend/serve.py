#!/usr/bin/env python3
"""
Simple HTTP Server for OERSync-AI Frontend

Serves the frontend HTML files on a local port.
"""

import http.server
import socketserver
import webbrowser
from pathlib import Path
import argparse
import sys

def start_server(port=3000, open_browser=True):
    """Start HTTP server for frontend"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    print(f"📁 Serving from: {frontend_dir}")
    
    # Setup handler
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🌐 Frontend läuft auf: http://localhost:{port}")
            print(f"📋 Stelle sicher, dass das Backend läuft: http://localhost:8000")
            print(f"⏹️  Zum Stoppen: Ctrl+C")
            
            if open_browser:
                webbrowser.open(f"http://localhost:{port}")
            
            # Serve files
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} ist bereits belegt.")
            print(f"💡 Versuche einen anderen Port: python serve.py --port 3001")
        else:
            print(f"❌ Fehler beim Starten des Servers: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Frontend-Server gestoppt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OERSync-AI Frontend Server")
    parser.add_argument("--port", "-p", type=int, default=3000, 
                       help="Port für Frontend-Server (default: 3000)")
    parser.add_argument("--no-browser", action="store_true",
                       help="Browser nicht automatisch öffnen")
    
    args = parser.parse_args()
    
    # Change to frontend directory before serving
    frontend_dir = Path(__file__).parent
    import os
    os.chdir(frontend_dir)
    
    start_server(port=args.port, open_browser=not args.no_browser) 