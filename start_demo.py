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
import psutil, os
class DemoManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        self.API_BASE_URL = os.environ.get("VITE_API_URL", "http://localhost:8000")
        self.FRONTEND_HOST = os.environ.get("FRONTEND_HOST", "localhost")

    def kill_process_on_port(self, port):
        """Kill any process using a specific port."""
        current_pid = os.getpid()

        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.pid:
                if conn.pid == current_pid:
                    continue
                try:
                    proc = psutil.Process(conn.pid)
                    print(f"⚠️  Killing process {proc.pid} ({proc.name()}) using port {port}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

    def start_backend(self):
        """Starte FastAPI Backend"""
        print("🚀 Starte Backend (FastAPI)...")

        # self.kill_process_on_port(8000)
        try:
            backend_dir = Path("services/extractor")
            self.backend_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=backend_dir,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )

            # Warte bis Backend bereit ist
            for i in range(15):  # 15 Sekunden timeout
                try:
                    import requests
                    response = requests.get(self.API_BASE_URL + "/health", timeout=1)
                    if response.status_code == 200:
                        print("✅ Backend läuft auf: " + self.API_BASE_URL)
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
            frontend_dir = Path("frontend-vite")
            # Prüfe ob npm installiert ist
            npm_check = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if npm_check.returncode != 0:
                print("❌ npm ist nicht installiert!")
                return False

            # Installiere Dependencies falls node_modules nicht existiert
            if not (frontend_dir / "node_modules").exists():
                print("📦 Installiere Frontend Dependencies...")
                npm_install = subprocess.run(["npm", "install"], cwd=frontend_dir, capture_output=True, text=True)
                if npm_install.returncode != 0:
                    print(f"❌ npm install fehlgeschlagen: {npm_install.stderr}")
                    return False

            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Warte bis Frontend bereit ist
            for i in range(15):  # 15 Sekunden timeout
                try:
                    import requests
                    # Versuche verschiedene Ports, da Vite automatisch wechselt
                    for port in [5173, 5174, 5175, 5176]:
                        try:
                            response = requests.get(f"http://localhost:{port}", timeout=1)
                            if response.status_code == 200:
                                print(f"✅ Frontend läuft auf: http://localhost:{port}")
                                return True
                        except:
                            continue
                except:
                    pass
                time.sleep(1)
                print(f"⏳ Warte auf Frontend... ({i+1}/15)")

            print("❌ Frontend konnte nicht gestartet werden")
            return False

        except Exception as e:
            print(f"❌ Fehler beim Starten des Frontends: {e}")
            return False

    def open_browser(self):
        """Öffne Browser mit Frontend"""
        print("🌐 Öffne Browser...")
        # Versuche verschiedene Ports zu finden
        for port in [5173, 5174, 5175, 5176]:
            try:
                import requests
                response = requests.get(f"http://localhost:{port}", timeout=1)
                if response.status_code == 200:
                    webbrowser.open(f"http://localhost:{port}")
                    return
            except:
                continue
        # Fallback auf Standard Vite Port
        webbrowser.open("http://localhost:5173")

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
        print("📱 Frontend: http://localhost:5173 (oder nächster verfügbarer Port)")
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