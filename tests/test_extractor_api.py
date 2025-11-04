#!/usr/bin/env python3
"""
Test Script für FastAPI Extractor Service

Testet alle API-Endpunkte des Extractor Service mit unserer echten MBZ-Datei.
"""
import os
import sys
from pathlib import Path
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))

# Configuration
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
API_BASE_URL = os.environ.get("VITE_API_URL", "http://localhost:8000")
MBZ_FILE_PATH = project_root / "063_PFB1.mbz"  # MBZ file is in project root

def print_response(response: requests.Response, title: str):
    """Formatierte Ausgabe einer HTTP-Response"""
    print(f"\n{'='*60}")
    print(f"📡 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    try:
        response_data = response.json()
        print(f"Response Body:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False, default=str))
    except:
        print(f"Response Body (raw): {response.text}")

def test_health_endpoint():
    """Test Health Check Endpoint"""
    print("\n🩺 TESTE HEALTH CHECK ENDPOINT")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print_response(response, "GET /health")

        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Check erfolgreich")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Version: {health_data.get('version')}")
            print(f"   Uptime: {health_data.get('uptime_seconds'):.2f}s")
            return True
        else:
            print(f"❌ Health Check fehlgeschlagen")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Verbindungsfehler: {e}")
        return False

def test_extract_upload():
    """Test MBZ File Upload"""
    print(f"\n📤 TESTE MBZ FILE UPLOAD")

    if not MBZ_FILE_PATH.exists():
        print(f"❌ MBZ-Datei nicht gefunden: {MBZ_FILE_PATH}")
        return None

    try:
        with open(MBZ_FILE_PATH, 'rb') as f:
            files = {'file': (MBZ_FILE_PATH.name, f, 'application/octet-stream')}
            response = requests.post(f"{API_BASE_URL}/extract", files=files, timeout=30)

        print_response(response, "POST /extract")

        if response.status_code == 200:
            upload_data = response.json()
            job_id = upload_data.get('job_id')
            print(f"✅ Upload erfolgreich")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {upload_data.get('status')}")
            print(f"   File Name: {upload_data.get('file_name')}")
            print(f"   File Size: {upload_data.get('file_size')} bytes")
            return job_id
        else:
            print(f"❌ Upload fehlgeschlagen")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Upload-Fehler: {e}")
        return None

def test_job_status(job_id: str):
    """Test Job Status Endpoint"""
    print(f"\n📊 TESTE JOB STATUS")

    try:
        response = requests.get(f"{API_BASE_URL}/extract/{job_id}/status", timeout=5)
        print_response(response, f"GET /extract/{job_id}/status")

        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Status-Abfrage erfolgreich")
            print(f"   Status: {status_data.get('status')}")
            print(f"   Message: {status_data.get('message')}")
            return status_data.get('status')
        else:
            print(f"❌ Status-Abfrage fehlgeschlagen")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Status-Abfrage Fehler: {e}")
        return None

def test_job_result(job_id: str):
    """Test Job Result Endpoint"""
    print(f"\n📋 TESTE JOB RESULT")

    try:
        response = requests.get(f"{API_BASE_URL}/extract/{job_id}", timeout=10)
        print_response(response, f"GET /extract/{job_id}")

        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Result-Abfrage erfolgreich")
            print(f"   Job ID: {result_data.get('job_id')}")
            print(f"   Status: {result_data.get('status')}")
            print(f"   Processing Time: {result_data.get('processing_time_seconds'):.2f}s")

            # Analysiere extracted_data
            extracted_data = result_data.get('extracted_data', {})
            if extracted_data:
                print(f"\n   📚 Extracted Data:")
                print(f"      Course: {extracted_data.get('course_name')}")
                print(f"      Course ID: {extracted_data.get('course_id')}")
                print(f"      Moodle Version: {extracted_data.get('moodle_version')}")

                # Dublin Core
                dublin_core = extracted_data.get('dublin_core', {})
                if dublin_core:
                    print(f"      🏛️  Dublin Core:")
                    print(f"         Title: {dublin_core.get('title')}")
                    print(f"         Language: {dublin_core.get('language')}")
                    print(f"         Type: {dublin_core.get('type')}")
                    print(f"         Creator: {dublin_core.get('creator')}")

                # Educational
                educational = extracted_data.get('educational', {})
                if educational:
                    print(f"      🎓 Educational:")
                    print(f"         Resource Type: {educational.get('learning_resource_type')}")
                    print(f"         Context: {educational.get('context')}")
                    print(f"         Difficulty: {educational.get('difficulty')}")

            return result_data

        elif response.status_code == 202:
            # Job noch in Bearbeitung
            status_data = response.json()
            print(f"⏳ Job noch in Bearbeitung")
            print(f"   Status: {status_data.get('status')}")
            print(f"   Message: {status_data.get('message')}")
            return "processing"

        else:
            print(f"❌ Result-Abfrage fehlgeschlagen")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Result-Abfrage Fehler: {e}")
        return None

def test_list_jobs():
    """Test List Jobs Endpoint"""
    print(f"\n📋 TESTE LIST JOBS")

    try:
        response = requests.get(f"{API_BASE_URL}/jobs", timeout=5)
        print_response(response, "GET /jobs")

        if response.status_code == 200:
            jobs_data = response.json()
            print(f"✅ Jobs-Liste erfolgreich abgerufen")
            print(f"   Anzahl Jobs: {len(jobs_data)}")

            for i, job in enumerate(jobs_data[:3]):  # Zeige max 3 Jobs
                print(f"   Job {i+1}:")
                print(f"      ID: {job.get('job_id')}")
                print(f"      Status: {job.get('status')}")
                print(f"      File: {job.get('file_name')}")
                print(f"      Created: {job.get('created_at')}")

            return jobs_data
        else:
            print(f"❌ Jobs-Liste Abfrage fehlgeschlagen")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Jobs-Liste Fehler: {e}")
        return None

def wait_for_job_completion(job_id: str, max_wait_time: int = 60) -> str:
    """Warte auf Job-Completion"""
    print(f"\n⏳ WARTE AUF JOB COMPLETION (max {max_wait_time}s)")

    start_time = time.time()

    while (time.time() - start_time) < max_wait_time:
        status = test_job_status(job_id)

        if status == "completed":
            print(f"✅ Job abgeschlossen nach {time.time() - start_time:.1f}s")
            return "completed"
        elif status == "failed":
            print(f"❌ Job fehlgeschlagen nach {time.time() - start_time:.1f}s")
            return "failed"
        elif status in ["pending", "processing"]:
            print(f"⏳ Job Status: {status} (nach {time.time() - start_time:.1f}s)")
            time.sleep(2)  # Warte 2 Sekunden
        else:
            print(f"❓ Unbekannter Status: {status}")
            break

    print(f"⏰ Timeout nach {max_wait_time}s erreicht")
    return "timeout"

def test_error_cases():
    """Test Error Cases"""
    print(f"\n🚨 TESTE ERROR CASES")

    # Test 1: Datei ohne .mbz Endung
    try:
        files = {'file': ('test.txt', b'not a zip file', 'text/plain')}
        response = requests.post(f"{API_BASE_URL}/extract", files=files, timeout=10)
        print_response(response, "POST /extract (wrong file type)")

        if response.status_code == 400:
            print(f"✅ Fehlerbehandlung für falsche Dateitypen funktioniert")
        else:
            print(f"⚠️  Unerwartete Response für falschen Dateityp")

    except Exception as e:
        print(f"❌ Fehler beim Test falscher Dateityp: {e}")

    # Test 2: Nicht-existente Job-ID
    try:
        fake_job_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{API_BASE_URL}/extract/{fake_job_id}", timeout=5)
        print_response(response, f"GET /extract/{fake_job_id} (fake job)")

        if response.status_code == 404:
            print(f"✅ Fehlerbehandlung für nicht-existente Jobs funktioniert")
        else:
            print(f"⚠️  Unerwartete Response für fake Job-ID")

    except Exception as e:
        print(f"❌ Fehler beim Test fake Job-ID: {e}")

def main():
    """Hauptfunktion für API-Tests"""
    print("🧪 TESTE OERSYNC-AI EXTRACTOR SERVICE API")
    print("=" * 80)

    print(f"🔗 Service URL: {API_BASE_URL}")
    print(f"📁 Test MBZ-Datei: {MBZ_FILE_PATH}")

    # Test 1: Health Check
    if not test_health_endpoint():
        print("❌ Service nicht erreichbar. Bitte prüfe ob der Service läuft:")
        print("   cd services/extractor && python main.py")
        return

    # Test 2: Upload MBZ File
    job_id = test_extract_upload()
    if not job_id:
        print("❌ Upload fehlgeschlagen. Tests werden abgebrochen.")
        return

    # Test 3: Job Status Monitoring
    final_status = wait_for_job_completion(job_id, max_wait_time=120)

    # Test 4: Job Result (wenn completed)
    if final_status == "completed":
        result = test_job_result(job_id)
        if result:
            print(f"✅ Vollständiger API-Test erfolgreich!")
        else:
            print(f"⚠️  Job completed aber Result-Abfrage fehlgeschlagen")
    elif final_status == "failed":
        # Versuche trotzdem Result abzufragen für Error-Details
        test_job_result(job_id)

    # Test 5: List Jobs
    test_list_jobs()

    # Test 6: Error Cases
    test_error_cases()

    # Zusammenfassung
    print(f"\n" + "="*80)
    print("📊 API TEST ZUSAMMENFASSUNG")
    print("="*80)

    if final_status == "completed":
        print(f"✅ Vollständiger API-Test erfolgreich!")
        print(f"   📤 Upload: Funktioniert")
        print(f"   ⚙️  Processing: Funktioniert")
        print(f"   📊 Status Monitoring: Funktioniert")
        print(f"   📋 Result Retrieval: Funktioniert")
        print(f"   🚨 Error Handling: Getestet")
    else:
        print(f"⚠️  API-Test teilweise erfolgreich")
        print(f"   📤 Upload: {'✅' if job_id else '❌'}")
        print(f"   ⚙️  Processing: {'❌' if final_status == 'failed' else '⏳'}")

    print(f"\n🔗 Weitere Tests möglich über:")
    print(f"   📖 API Docs: {API_BASE_URL}/docs")
    print(f"   📚 ReDoc: {API_BASE_URL}/redoc")

    print(f"\n🏁 API Test abgeschlossen!")

if __name__ == "__main__":
    main()