#!/usr/bin/env python3
"""
Test für die erweiterte Medienintegration in OERSync-AI

Testet das Parsing von files.xml und die Medienklassifizierung.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.mbz_extractor import MBZExtractor
from shared.utils.xml_parser import XMLParser, parse_moodle_backup_complete
from shared.models.dublin_core import (
    MediaType, FileMetadata, MediaCollection, 
    classify_media_type, create_media_collection_from_files
)


def test_media_type_classification():
    """Test der Medientyp-Klassifizierung"""
    print("\n" + "="*60)
    print("🎨 TESTE MEDIENTYP-KLASSIFIZIERUNG")
    print("="*60)
    
    test_cases = [
        # Bilder
        ("image/jpeg", "photo.jpg", MediaType.IMAGE),
        ("image/png", "screenshot.png", MediaType.IMAGE),
        ("image/gif", "animation.gif", MediaType.IMAGE),
        ("image/svg+xml", "icon.svg", MediaType.IMAGE),
        ("image/webp", "photo.webp", MediaType.IMAGE),
        
        # Videos
        ("video/mp4", "presentation.mp4", MediaType.VIDEO),
        ("video/avi", "tutorial.avi", MediaType.VIDEO),
        ("video/quicktime", "movie.mov", MediaType.VIDEO),
        ("video/x-ms-wmv", "video.wmv", MediaType.VIDEO),
        ("video/webm", "web_video.webm", MediaType.VIDEO),
        
        # Audio
        ("audio/mpeg", "music.mp3", MediaType.AUDIO),
        ("audio/wav", "sound.wav", MediaType.AUDIO),
        ("audio/ogg", "audio.ogg", MediaType.AUDIO),
        ("audio/aac", "podcast.aac", MediaType.AUDIO),
        ("audio/flac", "high_quality.flac", MediaType.AUDIO),
        
        # Dokumente
        ("application/pdf", "document.pdf", MediaType.DOCUMENT),
        ("text/plain", "readme.txt", MediaType.DOCUMENT),
        ("text/html", "page.html", MediaType.DOCUMENT),
        ("application/msword", "document.doc", MediaType.DOCUMENT),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "document.docx", MediaType.DOCUMENT),
        
        # Präsentationen
        ("application/vnd.ms-powerpoint", "presentation.ppt", MediaType.PRESENTATION),
        ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "presentation.pptx", MediaType.PRESENTATION),
        
        # Tabellen
        ("application/vnd.ms-excel", "data.xls", MediaType.SPREADSHEET),
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data.xlsx", MediaType.SPREADSHEET),
        
        # Archive
        ("application/zip", "archive.zip", MediaType.ARCHIVE),
        ("application/x-rar-compressed", "archive.rar", MediaType.ARCHIVE),
        ("application/x-7z-compressed", "archive.7z", MediaType.ARCHIVE),
        ("application/x-tar", "archive.tar", MediaType.ARCHIVE),
        ("application/gzip", "archive.gz", MediaType.ARCHIVE),
        
        # Code
        ("text/x-python", "script.py", MediaType.CODE),
        ("application/javascript", "script.js", MediaType.CODE),
        ("text/html", "style.css", MediaType.CODE),
        ("text/x-java-source", "Main.java", MediaType.CODE),
        ("text/x-c++src", "main.cpp", MediaType.CODE),
        ("text/x-php", "script.php", MediaType.CODE),
        ("text/x-sql", "database.sql", MediaType.CODE),
        
        # Unbekannte Typen
        ("application/octet-stream", "unknown.bin", MediaType.OTHER),
        ("text/unknown", "mystery.xyz", MediaType.OTHER),
    ]
    
    passed = 0
    failed = 0
    
    for mimetype, filename, expected_type in test_cases:
        try:
            result = classify_media_type(mimetype, filename)
            if result == expected_type:
                print(f"✅ {filename} ({mimetype}) -> {result.value}")
                passed += 1
            else:
                print(f"❌ {filename} ({mimetype}) -> {result.value} (erwartet: {expected_type.value})")
                failed += 1
        except Exception as e:
            print(f"❌ {filename} ({mimetype}) -> Fehler: {e}")
            failed += 1
    
    print(f"\n📊 Ergebnisse: {passed} bestanden, {failed} fehlgeschlagen")
    return failed == 0


def test_file_metadata_creation():
    """Test der FileMetadata-Erstellung"""
    print("\n" + "="*60)
    print("📄 TESTE FILEMETADATA-ERSTELLUNG")
    print("="*60)
    
    try:
        # Erstelle eine Test-FileMetadata
        file_metadata = FileMetadata(
            file_id="a1b2c3d4e5f6789012345678901234567890abcd",
            original_filename="test_image.jpg",
            filepath="/course_files/images/",
            mimetype="image/jpeg",
            filesize=1024000,
            media_type=MediaType.IMAGE,
            file_extension=".jpg",
            title="Test Image",
            description="Ein Testbild",
            author="Test User",
            is_image=True,
            is_video=False,
            is_document=False,
            is_audio=False,
            timecreated=datetime.now(),
            timemodified=datetime.now()
        )
        
        print(f"✅ FileMetadata erstellt:")
        print(f"   📁 Datei: {file_metadata.original_filename}")
        print(f"   🆔 ID: {file_metadata.file_id}")
        print(f"   📊 Größe: {file_metadata.filesize} Bytes")
        print(f"   🎨 Typ: {file_metadata.media_type.value}")
        print(f"   📝 Titel: {file_metadata.title}")
        print(f"   👤 Autor: {file_metadata.author}")
        
        # Teste Serialisierung
        file_dict = file_metadata.dict()
        print(f"   🔄 Serialisierung: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei FileMetadata-Erstellung: {e}")
        return False


def test_media_collection_creation():
    """Test der MediaCollection-Erstellung"""
    print("\n" + "="*60)
    print("📚 TESTE MEDIACOLLECTION-ERSTELLUNG")
    print("="*60)
    
    try:
        # Erstelle Test-Dateien
        test_files = [
            FileMetadata(
                file_id=f"file_{i}",
                original_filename=f"test_{i}.jpg",
                filepath="/course_files/",
                mimetype="image/jpeg",
                filesize=1024 * (i + 1),
                media_type=MediaType.IMAGE,
                file_extension=".jpg",
                is_image=True,
                is_video=False,
                is_document=False,
                is_audio=False
            )
            for i in range(5)
        ]
        
        # Füge verschiedene Medientypen hinzu
        test_files.extend([
            FileMetadata(
                file_id="video_1",
                original_filename="video.mp4",
                filepath="/course_files/",
                mimetype="video/mp4",
                filesize=10240000,
                media_type=MediaType.VIDEO,
                file_extension=".mp4",
                is_image=False,
                is_video=True,
                is_document=False,
                is_audio=False
            ),
            FileMetadata(
                file_id="doc_1",
                original_filename="document.pdf",
                filepath="/course_files/",
                mimetype="application/pdf",
                filesize=512000,
                media_type=MediaType.DOCUMENT,
                file_extension=".pdf",
                is_image=False,
                is_video=False,
                is_document=True,
                is_audio=False
            )
        ])
        
        # Erstelle MediaCollection
        collection = create_media_collection_from_files(
            test_files,
            "test_collection",
            "Test Media Collection"
        )
        
        print(f"✅ MediaCollection erstellt:")
        print(f"   📚 Name: {collection.name}")
        print(f"   📊 Gesamtdateien: {collection.total_files}")
        print(f"   💾 Gesamtgröße: {collection.total_size} Bytes")
        print(f"   🖼️  Bilder: {len(collection.images)}")
        print(f"   🎥 Videos: {len(collection.videos)}")
        print(f"   📄 Dokumente: {len(collection.documents)}")
        print(f"   🎵 Audio: {len(collection.audio_files)}")
        print(f"   📦 Sonstige: {len(collection.other_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei MediaCollection-Erstellung: {e}")
        return False


def test_files_xml_parsing():
    """Test des files.xml Parsings"""
    print("\n" + "="*60)
    print("📋 TESTE FILES.XML PARSING")
    print("="*60)
    
    # Erstelle eine Test-files.xml
    test_files_xml = """<?xml version="1.0" encoding="UTF-8"?>
<files>
    <file>
        <contenthash>a1b2c3d4e5f6789012345678901234567890abcd</contenthash>
        <filename>test_image.jpg</filename>
        <filepath>/course_files/images/</filepath>
        <mimetype>image/jpeg</mimetype>
        <filesize>1024000</filesize>
        <timecreated>1642233600</timecreated>
        <timemodified>1642233600</timemodified>
        <userid>1</userid>
        <source>draft</source>
        <author>Test User</author>
        <license>CC BY</license>
    </file>
    <file>
        <contenthash>b2c3d4e5f6789012345678901234567890abcde1</contenthash>
        <filename>presentation.pdf</filename>
        <filepath>/course_files/documents/</filepath>
        <mimetype>application/pdf</mimetype>
        <filesize>2048000</filesize>
        <timecreated>1642233600</timecreated>
        <timemodified>1642233600</timemodified>
        <userid>1</userid>
        <source>draft</source>
    </file>
    <file>
        <contenthash>c3d4e5f6789012345678901234567890abcde12</contenthash>
        <filename>video.mp4</filename>
        <filepath>/course_files/videos/</filepath>
        <mimetype>video/mp4</mimetype>
        <filesize>10485760</filesize>
        <timecreated>1642233600</timecreated>
        <timemodified>1642233600</timemodified>
        <userid>1</userid>
        <source>draft</source>
    </file>
</files>"""
    
    try:
        # Erstelle temporäre files.xml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(test_files_xml)
            temp_xml_path = Path(f.name)
        
        # Parse files.xml
        parser = XMLParser()
        files_info = parser.parse_files_xml(temp_xml_path)
        
        print(f"✅ Files.xml erfolgreich geparst:")
        print(f"   📄 Gefundene Dateien: {len(files_info)}")
        
        for i, file_info in enumerate(files_info, 1):
            print(f"   📁 Datei {i}: {file_info.original_filename}")
            print(f"      🆔 ID: {file_info.file_id}")
            print(f"      📊 Größe: {file_info.filesize} Bytes")
            print(f"      🎨 MIME-Type: {file_info.mimetype}")
            print(f"      📍 Pfad: {file_info.filepath}")
        
        # Teste Konvertierung zu FileMetadata
        file_metadata_list = parser.convert_files_to_metadata(files_info)
        
        print(f"\n🔄 Konvertierung zu FileMetadata:")
        print(f"   📄 Konvertierte Dateien: {len(file_metadata_list)}")
        
        for file_meta in file_metadata_list:
            print(f"   🎨 {file_meta.original_filename} -> {file_meta.media_type.value}")
        
        # Teste Statistiken
        statistics = parser.create_file_statistics(file_metadata_list)
        
        print(f"\n📊 Statistiken:")
        print(f"   📄 Gesamtdateien: {statistics['total_files']}")
        print(f"   💾 Gesamtgröße: {statistics['total_size']} Bytes")
        print(f"   🎨 Nach Typ: {list(statistics['by_type'].keys())}")
        
        # Cleanup
        temp_xml_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim files.xml Parsing: {e}")
        if 'temp_xml_path' in locals():
            temp_xml_path.unlink()
        return False


def test_complete_media_integration():
    """Test der vollständigen Medienintegration"""
    print("\n" + "="*60)
    print("🚀 TESTE VOLLSTÄNDIGE MEDIENINTEGRATION")
    print("="*60)
    
    # Prüfe ob MBZ-Datei vorhanden ist
    mbz_path = project_root / "063_PFB1.mbz"
    if not mbz_path.exists():
        print(f"⚠️  MBZ-Datei nicht gefunden: {mbz_path}")
        print("   Überspringe vollständigen Integrationstest")
        return True
    
    try:
        # Extrahiere MBZ
        temp_dir = Path(tempfile.mkdtemp(prefix="media_test_"))
        extractor = MBZExtractor(temp_dir)
        extraction_result = extractor.extract_mbz(mbz_path)
        
        print(f"✅ MBZ extrahiert: {extraction_result.temp_dir}")
        
        # Prüfe ob files.xml vorhanden ist
        if not extraction_result.files_xml or not extraction_result.files_xml.exists():
            print("⚠️  files.xml nicht gefunden in MBZ")
            print("   Überspringe vollständigen Integrationstest")
            return True
        
        # Parse mit vollständiger Medienintegration
        extracted_data = parse_moodle_backup_complete(
            backup_xml_path=extraction_result.moodle_backup_xml,
            course_xml_path=extraction_result.course_xml,
            sections_path=extraction_result.temp_dir / "extracted" / "sections" if (extraction_result.temp_dir / "extracted" / "sections").exists() else None,
            activities_path=extraction_result.temp_dir / "extracted" / "activities" if (extraction_result.temp_dir / "extracted" / "activities").exists() else None,
            files_xml_path=extraction_result.files_xml
        )
        
        print(f"✅ Vollständige Extraktion mit Medienintegration:")
        print(f"   📚 Kurs: {extracted_data.course_name}")
        print(f"   📄 Dateien: {len(extracted_data.files)}")
        print(f"   📚 Sammlungen: {len(extracted_data.media_collections)}")
        
        # Zeige Dateistatistiken
        if extracted_data.file_statistics:
            stats = extracted_data.file_statistics
            print(f"   📊 Statistiken:")
            print(f"      📄 Gesamtdateien: {stats.get('total_files', 0)}")
            print(f"      💾 Gesamtgröße: {stats.get('total_size', 0)} Bytes")
            
            by_type = stats.get('by_type', {})
            if by_type:
                print(f"      🎨 Nach Typ:")
                for media_type, data in by_type.items():
                    print(f"         {media_type}: {data.get('count', 0)} Dateien")
        
        # Zeige Beispiele für verschiedene Medientypen
        if extracted_data.files:
            print(f"   🎨 Medientyp-Beispiele:")
            type_examples = {}
            for file_meta in extracted_data.files:
                media_type = file_meta.media_type.value
                if media_type not in type_examples:
                    type_examples[media_type] = file_meta.original_filename
            
            for media_type, filename in type_examples.items():
                print(f"      {media_type}: {filename}")
        
        # Cleanup
        extractor.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei vollständiger Medienintegration: {e}")
        if 'extractor' in locals():
            extractor.cleanup()
        return False


def main():
    """Hauptfunktion für alle Medienintegration-Tests"""
    print("🧪 TESTE OERSYNC-AI MEDIENINTEGRATION")
    print("=" * 80)
    
    tests = [
        ("Medientyp-Klassifizierung", test_media_type_classification),
        ("FileMetadata-Erstellung", test_file_metadata_creation),
        ("MediaCollection-Erstellung", test_media_collection_creation),
        ("Files.xml Parsing", test_files_xml_parsing),
        ("Vollständige Medienintegration", test_complete_media_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Führe Test aus: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test fehlgeschlagen: {e}")
            results.append((test_name, False))
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("📊 TEST-ZUSAMMENFASSUNG")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Gesamtergebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Medienintegration-Tests erfolgreich!")
        return True
    else:
        print("⚠️  Einige Tests fehlgeschlagen")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 