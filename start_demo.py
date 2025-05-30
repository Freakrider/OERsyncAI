#!/usr/bin/env python3
"""
🎓 OERSync-AI Demo Starter

Startet Backend und Frontend gleichzeitig für eine komplette Demo.
"""

import subprocess
import time
import webbrowser
import sys
import signal
from pathlib import Path
import threading

class DemoManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
    def start_backend(self):
        """Starte FastAPI Backend"""
        print("🚀 Starte Backend (FastAPI)...")
        try:
            backend_dir = Path("services/extractor")
            self.backend_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Warte bis Backend bereit ist
            for i in range(15):  # 15 Sekunden timeout
                try:
                    import requests
                    response = requests.get("http://localhost:8000/health", timeout=1)
                    if response.status_code == 200:
                        print("✅ Backend läuft auf: http://localhost:8000")
                        return True
                except:
                    time.sleep(1)
                    print(f"⏳ Warte auf Backend... ({i+1}/15)")
            
            print("❌ Backend konnte nicht gestartet werden")
            return False
            
        except Exception as e:
            print(f"❌ Fehler beim Starten des Backends: {e}")
            return False
    
    def start_frontend(self):
        """Starte Frontend Server"""
        print("🌐 Starte Frontend...")
        try:
            frontend_dir = Path("frontend")
            self.frontend_process = subprocess.Popen(
                [sys.executable, "serve.py", "--no-browser"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Warte kurz bis Frontend bereit ist
            time.sleep(2)
            print("✅ Frontend läuft auf: http://localhost:3000")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Starten des Frontends: {e}")
            return False
    
    def open_browser(self):
        """Öffne Browser mit Frontend"""
        print("🌐 Öffne Browser...")
        webbrowser.open("http://localhost:3000")
    
    def stop_services(self):
        """Stoppe alle Services"""
        print("\n🛑 Stoppe Services...")
        
        if self.backend_process:
            self.backend_process.terminate()
            print("✅ Backend gestoppt")
            
        if self.frontend_process:
            self.frontend_process.terminate()
            print("✅ Frontend gestoppt")
    
    def run_demo(self):
        """Starte komplette Demo"""
        print("=" * 60)
        print("🎓 OERSync-AI Demo Starter")
        print("=" * 60)
        
        # Signal handler für Clean Shutdown
        def signal_handler(sig, frame):
            print("\n⚠️  Shutdown Signal empfangen...")
            self.stop_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Starte Services
        if not self.start_backend():
            return False
            
        if not self.start_frontend():
            self.stop_services()
            return False
        
        # Öffne Browser
        self.open_browser()
        
        print("\n" + "=" * 60)
        print("🎉 Demo läuft!")
        print("=" * 60)
        print("📱 Frontend: http://localhost:3000")
        print("⚡ Backend:  http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("=" * 60)
        print("📋 Zum Testen:")
        print("   1. MBZ-Datei per Drag & Drop hochladen")
        print("   2. Metadaten werden automatisch extrahiert")
        print("   3. Ergebnisse werden schön angezeigt")
        print("=" * 60)
        print("⏹️  Zum Stoppen: Ctrl+C")
        print("=" * 60)
        
        # Warte auf User Input
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_services()

def check_dependencies():
    """Prüfe ob alle Dependencies vorhanden sind"""
    print("🔍 Prüfe Dependencies...")
    
    # Prüfe Virtual Environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Virtual Environment nicht aktiviert!")
        print("💡 Führe aus: source venv/bin/activate")
        return False
    
    # Prüfe MBZ Test-Datei
    if not Path("063_PFB1.mbz").exists():
        print("⚠️  Test-MBZ-Datei nicht gefunden!")
        print("💡 Lade eine MBZ-Datei herunter oder verwende eine eigene")
        # return False  # Nicht kritisch, User kann eigene Datei hochladen
    
    try:
        import fastapi, uvicorn, requests
        print("✅ Alle Dependencies gefunden")
        return True
    except ImportError as e:
        print(f"❌ Fehlende Dependency: {e}")
        print("💡 Führe aus: pip install -e .")
        return False

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    
    demo = DemoManager()
    demo.run_demo() 