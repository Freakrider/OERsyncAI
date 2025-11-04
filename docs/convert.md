# ILIAS zu Moodle Konvertierung - Analyse und Probleme

## Übersicht

Dieses Dokument analysiert die Konvertierung von ILIAS-Kursen zu Moodle-Backup-Dateien (MBZ) und identifiziert die aktuellen Probleme sowie nächste Schritte zur Verbesserung.

**Stand**: November 2025  
**Analysierte Beispiele**:
- ILIAS: `dummy_files/ilias_kurs/`
- Moodle: `dummy_files/Moodle_Adaptive_Kursvorlage_Stufe1_Februar2025/`

---

## 1. Strukturelle Unterschiede zwischen ILIAS und Moodle

### 1.1 ILIAS Kursstruktur

**Hierarchie**:
```
Kurs (grp - Group)
  └─ Container (Services/Container/export.xml)
       ├─ Item: Test (tst)
       ├─ Item: Test Wiederholung (tst)
       ├─ Item: Ankerelement Gratifikation (fold - Folder)
       ├─ Item: Datei (itgr - ItemGroup)
       │    └─ ItgrItem: 9193, 9194, 9197, 9200, 9294, 9674, 9732
       ├─ Item: Self-Assessment 1 (itgr)
       ├─ Item: Self-Assessment 1 - Wiederholung (itgr)
       └─ Item: Video (itgr)
```

**ILIAS Typen**:
- `grp` (Group): Hauptcontainer für einen Kurs
- `fold` (Folder): Ordner/Gruppierung von Inhalten
- `itgr` (ItemGroup): Gruppierung von Items (z.B. mehrere Dateien unter einem Titel)
- `tst` (Test): Test/Quiz
- `file`: Einzelne Datei
- `mcst` (MediaCast): Video/Audio-Inhalte

**Besonderheit**: Die Container-Structure (`Services/Container/set_1/export.xml`) enthält die **komplette Struktur** mit allen Items, RefIds, Titeln und Typen.

### 1.2 Moodle Kursstruktur

**Hierarchie**:
```
Kurs
  ├─ Section 345: "Kursinformationen" (number=0)
  │    ├─ Activity: label_1981 (Einführung)
  │    └─ Activity: page_1982 (Schritt 1: Vorlagen-Nutzungshinweise)
  ├─ Section 346: ""Thema" einfügen"
  │    ├─ Activity: page_1983 (Schritt 2: Wissensinhalt einfügen)
  │    ├─ Activity: quiz_1984 (Schritt 3: Wissensüberprüfung)
  │    └─ Activity: page_1985 (Schritt 4: Adaptiven Inhalt erstellen)
  └─ Section 348: "Abschluss"
       └─ Activity: page_2053 (Schritt 5: Kursabschluss)
```

**Moodle Typen**:
- `label`: Text-Label ohne separaten Link
- `page`: Inhaltsseite
- `quiz`: Test/Quiz
- `resource`: Datei oder Link
- `folder`: Ordner mit mehreren Dateien
- `forum`: Forum
- `assign`: Aufgabe

**Besonderheit**: Sections haben **semantische Namen** wie "Kursinformationen", ""Thema" einfügen", die die logische Struktur widerspiegeln.

---

## 2. Aktuelle Converter-Implementierung

### 2.1 Analyzer (`analyzer.py`)

**Was funktioniert**:
- ✅ Parst die `manifest.xml` und findet Export-Sets
- ✅ Analysiert Komponenten (grp, tst, mcst, file, itgr)
- ✅ Erstellt Module aus Komponenten
- ✅ Extrahiert Titel und Metadaten aus `export.xml`

**Probleme**:
- ❌ Erstellt für **jede Komponente ein eigenes Modul** (flache Struktur)
- ❌ Ignoriert die **hierarchische Container-Struktur** aus `Services/Container/export.xml`
- ❌ Keine Erkennung von **logischen Gruppierungen** (z.B. "Kursinformationen" vs. "Thema")
- ❌ Folder (fold) und ItemGroups (itgr) werden als eigenständige Module behandelt, statt als Sections

**Code-Stelle**:
```python
# analyzer.py, Zeile 391-601
def _create_modules_from_components(self) -> None:
    # Problem: Erstellt ein Modul pro Komponente
    for component in self.components:
        module = self.add_module(
            id=comp_data.get("id", ""),
            title=comp_data.get("title", f"{comp_type.upper()} ohne Titel"),
            type=comp_type
        )
```

### 2.2 Moodle Converter (`moodle_converter.py`)

**Was funktioniert**:
- ✅ Erstellt valide Moodle-Backup-Struktur (XML-Dateien)
- ✅ Konvertiert ILIAS-Typen zu Moodle-Typen
- ✅ Generiert MBZ-Datei

**Probleme**:
- ❌ **Section-Zuordnung basiert nur auf Module-Index**, nicht auf Inhalt
  ```python
  # moodle_converter.py, Zeile 221-248
  for module_index, module in enumerate(self.analyzer.modules, 1):
      for item_index, item in enumerate(module.items, 1):
          # Problem: sectionid = module_index
          sectionid = ET.SubElement(activity, 'sectionid')
          sectionid.text = str(module_index)
  ```
- ❌ **Section-Titel werden aus Module-Titeln generiert**, keine semantische Kategorisierung
  ```python
  # moodle_converter.py, Zeile 556-570
  for i, module in enumerate(self.analyzer.modules, 1):
      section_name = ET.SubElement(section, 'name')
      section_name.text = module.title  # <-- Nicht "Kursinformationen"!
  ```
- ❌ Kein Mapping für spezielle Sections wie "Allgemein", "Kursinformationen", "Abschluss"
- ❌ **ItemGroups werden nicht korrekt aufgelöst** - Items in einer ItemGroup sollten Activities sein, nicht die ItemGroup selbst

### 2.3 Typ-Mapping

**Aktuelles Mapping** (`moodle_converter.py`, Zeile 366-381):
```python
activity_mapping = {
    'file': 'resource',
    'documents': 'resource',
    'presentations': 'resource',
    'forum': 'forum',
    'test': 'quiz',
    'exercise': 'assign',
    'wiki': 'wiki',
    'mediacast': 'resource',
    'itemgroup': 'folder'  # <-- Problem: ItemGroup ist keine Activity!
}
```

**Problem**: `itemgroup` sollte keine Activity sein, sondern die Items darin sollten zu Activities werden.

---

## 3. Konkrete Probleme beim Konvertieren

### Problem 1: Fehlende Section-Kategorisierung

**Was passiert**:
```
ILIAS Input:
- Group: "Vorlage: Adaptivitätsstufe 1 (Learning Nugget)"
  - Folder: "Ankerelement Gratifikation"
  - ItemGroup: "Datei"
  - ItemGroup: "Self-Assessment 1"
  - ItemGroup: "Video"

Aktueller Output:
- Section 1: "Vorlage: Adaptivitätsstufe 1 (Learning Nugget)" <-- Gruppe wird Section
- Section 2: "Ankerelement Gratifikation" <-- Folder wird Section
- Section 3: "Datei" <-- ItemGroup wird Section
- Section 4: "Self-Assessment 1"
- Section 5: "Video"
```

**Was sein sollte**:
```
Erwarteter Output (analog zu Moodle-Vorlage):
- Section 0: "Allgemein" (automatisch)
- Section 1: "Kursinformationen" <-- Logische Gruppierung
  - Activity: Einführungstext
  - Activity: Anweisungen für Lehrende
- Section 2: "Wissensinhalt" <-- Logische Gruppierung
  - Activity: Datei
  - Activity: Self-Assessment
  - Activity: Video
- Section 3: "Abschluss"
  - Activity: Gratifikation
```

### Problem 2: ItemGroups nicht aufgelöst

**ILIAS Input** (`set_3/.../export.xml`):
```xml
<ItemGroup>
  <Id>9125</Id>
  <Title>Datei</Title>
  <ItgrItem><ItemId>9193</ItemId></ItgrItem>
  <ItgrItem><ItemId>9194</ItemId></ItgrItem>
  <ItgrItem><ItemId>9197</ItemId></ItgrItem>
  ...
</ItemGroup>
```

**Aktueller Output**:
- Ein Modul "Datei" (type=itgr)
- Mit Items: `item_0`, `item_1`, ... (Metadata enthält nur IDs)

**Was sein sollte**:
- **Keine eigene Activity** für die ItemGroup
- Stattdessen: Die **einzelnen Items** (9193, 9194, ...) sollten als separate Activities exportiert werden
- Diese Activities sollten in der **gleichen Section** sein

### Problem 3: Fehlende Container-Struktur-Nutzung

Die Datei `Services/Container/set_1/export.xml` enthält die **komplette Struktur** mit allen RefIds und Hierarchien:

```xml
<Item RefId="3812" Id="9094" Title="Vorlage..." Type="grp">
  <Item RefId="3845" Id="9151" Title="Test" Type="tst"/>
  <Item RefId="3826" Id="9124" Title="Ankerelement Gratifikation" Type="fold"/>
  <Item RefId="3827" Id="9125" Title="Datei" Type="itgr"/>
  ...
</Item>
```

**Problem**: Diese Struktur wird **nicht genutzt** für die Section-Zuordnung!

### Problem 4: Keine Titel-Übersetzung

ILIAS-Titel wie "Vorlage: Adaptivitätsstufe 1 (Learning Nugget)" sollten zu sinnvollen Moodle-Section-Namen werden:
- "Kursinformationen" (wenn es eine Einführung ist)
- "Wissensinhalt" (für Lernmaterialien)
- "Abschluss" (für Gratifikation/Zusammenfassung)

---

## 4. Lösungsansätze

### 4.1 Container-Struktur-Parser

**Neue Klasse**: `ContainerStructureParser`

```python
class ContainerStructureParser:
    """
    Parst die Container-Struktur aus Services/Container/export.xml
    und erstellt eine hierarchische Struktur.
    """
    
    def parse(self, export_xml_path: str) -> ContainerStructure:
        # Liest die Container-Struktur
        # Gibt zurück: Hierarchie mit RefIds, Typen, Titeln
        pass
    
    def map_to_sections(self, structure: ContainerStructure) -> List[Section]:
        # Mappt die Struktur zu Moodle-Sections
        # Logik:
        # 1. Folder (fold) → Könnte eine Section sein
        # 2. ItemGroup (itgr) → Items darin werden Activities
        # 3. Tests (tst) → Activities
        pass
```

### 4.2 Section-Kategorisierer

**Neue Klasse**: `SectionCategorizer`

```python
class SectionCategorizer:
    """
    Kategorisiert ILIAS-Items in sinnvolle Moodle-Sections.
    """
    
    CATEGORY_KEYWORDS = {
        'introduction': ['einführung', 'anleitung', 'hinweis', 'vorlage'],
        'content': ['datei', 'selbst', 'assessment', 'video', 'wissen'],
        'conclusion': ['abschluss', 'gratifikation', 'anker']
    }
    
    def categorize(self, items: List[Item]) -> Dict[str, List[Item]]:
        # Kategorisiert Items basierend auf Titel/Typ
        # Gibt zurück: {"introduction": [...], "content": [...], ...}
        pass
    
    def generate_section_name(self, category: str) -> str:
        # Generiert deutschen Section-Namen
        # "introduction" → "Kursinformationen"
        # "content" → "Wissensinhalt"
        # "conclusion" → "Abschluss"
        pass
```

### 4.3 ItemGroup-Resolver

**Neue Klasse**: `ItemGroupResolver`

```python
class ItemGroupResolver:
    """
    Löst ItemGroups auf und findet die referenzierten Items.
    """
    
    def resolve(self, itemgroup: ItemGroup, all_components: List[Component]) -> List[Item]:
        # Findet die Items mit den IDs aus der ItemGroup
        # Gibt zurück: Liste von Items, die als Activities exportiert werden
        pass
```

### 4.4 Verbesserter Workflow

**Neuer Ablauf**:
```
1. Analyzer analysiert Komponenten (wie bisher)
   └─ Aber: Speichert auch Container-Struktur

2. ContainerStructureParser parst die Hierarchie
   └─ Erstellt Baum mit allen Items und Referenzen

3. ItemGroupResolver löst ItemGroups auf
   └─ Ersetzt ItemGroups durch ihre tatsächlichen Items

4. SectionCategorizer kategorisiert Items
   └─ Gruppiert nach "Kursinformationen", "Wissensinhalt", etc.

5. MoodleConverter erstellt Sections + Activities
   └─ Nutzt die kategorisierten Gruppen für Section-Namen
```

---

## 5. Nächste Schritte

### Phase 1: Container-Struktur verstehen ✅
- [x] ILIAS-Struktur analysieren
- [x] Moodle-Struktur analysieren
- [x] Probleme identifizieren

### Phase 2: Parser erweitern
- [ ] `ContainerStructureParser` implementieren
  - Container-XML parsen
  - Hierarchie extrahieren
  - RefIds zu Komponenten auflösen
- [ ] Tests schreiben für Container-Parsing

### Phase 3: ItemGroup-Handling
- [ ] `ItemGroupResolver` implementieren
  - ItemGroup-Items zu realen Komponenten auflösen
  - Mapping RefId → Komponente
- [ ] Tests für ItemGroup-Auflösung

### Phase 4: Section-Kategorisierung
- [ ] `SectionCategorizer` implementieren
  - Keyword-basierte Kategorisierung
  - Deutsche Section-Namen generieren
- [ ] Konfigurationsdatei für Kategorien (YAML/JSON)

### Phase 5: Converter-Integration
- [ ] `MoodleConverter` anpassen
  - Nutze kategorisierte Sections
  - Erstelle korrekte Section-Namen
  - Ordne Activities zu Sections zu
- [ ] End-to-End Tests mit Beispielkursen

### Phase 6: Preview-Integration
- [ ] Frontend anpassen
  - Zeige Sections gruppiert
  - Zeige Activity-Typen mit Icons
- [ ] API anpassen für strukturierte Daten

---

## 6. Offene Fragen

1. **Section-Zuordnung**: Soll es eine Konfiguration geben, wie Items zu Sections zugeordnet werden?
   - Beispiel: "Alle ItemGroups mit 'Self-Assessment' im Namen → Section 'Wissensinhalt'"

2. **Mehrsprachigkeit**: Wie gehen wir mit nicht-deutschen Kursen um?
   - Aktuell sind die Keywords auf Deutsch
   - Brauchen wir i18n?

3. **Nested Structures**: Wie gehen wir mit verschachtelten Folders um?
   - ILIAS erlaubt Folder in Folders
   - Moodle hat nur eine Section-Ebene
   - Sollten wir Sub-Folders flach machen?

4. **RefId-Auflösung**: Wie finden wir die Komponente zu einer RefId?
   - Aktuell haben wir nur Component-IDs
   - RefIds sind in der Container-Struktur
   - Brauchen wir ein Mapping RefId → Component?

5. **Timing-Informationen**: Die Container-Struktur enthält Timing-Daten (Start/End). Sollen diese übernommen werden?
   - Moodle unterstützt auch Verfügbarkeitseinschränkungen
   - Wie mappen wir ILIAS Timing → Moodle Availability?

---

## 7. Code-Änderungen (Übersicht)

### Neue Dateien
- `shared/utils/ilias/container_parser.py`: Container-Struktur-Parser
- `shared/utils/ilias/itemgroup_resolver.py`: ItemGroup-Resolver
- `shared/utils/ilias/section_categorizer.py`: Section-Kategorisierer
- `shared/utils/ilias/section_mapping.yaml`: Konfiguration für Section-Mapping

### Zu ändernde Dateien
- `shared/utils/ilias/analyzer.py`:
  - `_analyze_export_set()`: Parse auch Container-Struktur
  - `_create_modules_from_components()`: Nutze Container-Struktur
- `shared/utils/ilias/moodle_converter.py`:
  - `_create_moodle_backup_xml()`: Nutze kategorisierte Sections
  - `_create_sections_xml()`: Generiere sinnvolle Section-Namen
  - `_create_activity_xmls()`: Ordne zu korrekten Sections zu
- `shared/utils/ilias/factory.py`:
  - Registriere neue Parser

### Tests
- `tests/test_container_parser.py`: Tests für Container-Parsing
- `tests/test_itemgroup_resolver.py`: Tests für ItemGroup-Auflösung
- `tests/test_section_categorizer.py`: Tests für Kategorisierung
- `tests/test_ilias_to_moodle_conversion.py`: End-to-End Tests

---

## 8. Beispiel: Erwartete Konvertierung

### Input: ILIAS Kurs "Vorlage: Adaptivitätsstufe 1"

**Struktur** (aus Container-XML):
```
Group: "Vorlage: Adaptivitätsstufe 1 (Learning Nugget)"
├─ Test: "Test"
├─ Test: "Test Wiederholung"
├─ Folder: "Ankerelement Gratifikation"
├─ ItemGroup: "Datei"
│   ├─ File: "Fernglas.jpg"
│   ├─ File: "02_Sanduhr_anthrazit_100_var.svg"
│   └─ ...
├─ ItemGroup: "Self-Assessment 1"
│   └─ (Items...)
├─ ItemGroup: "Self-Assessment 1 - Wiederholung"
│   └─ (Items...)
└─ ItemGroup: "Video"
    └─ (Items...)
```

### Output: Moodle Sections + Activities

```
Section 0: "Allgemein" (leer, Moodle-Standard)

Section 1: "Kursinformationen"
  - label: "Einführung: Vorlage: Adaptivitätsstufe 1 (Learning Nugget)"
  - page: "Anweisungen für Lehrende"

Section 2: "Wissensinhalt"
  - resource: "Fernglas.jpg"
  - resource: "02_Sanduhr_anthrazit_100_var.svg"
  - quiz: "Self-Assessment 1"
  - resource: "Video-Inhalte"

Section 3: "Wiederholung"
  - quiz: "Test"
  - quiz: "Test Wiederholung"
  - quiz: "Self-Assessment 1 - Wiederholung"

Section 4: "Abschluss"
  - folder: "Ankerelement Gratifikation"
```

---

## 9. Technische Details

### Container-XML-Struktur

Die `Services/Container/set_1/export.xml` hat folgende Struktur:

```xml
<exp:Export>
  <exp:ExportItem Id="9094">
    <Items>
      <Item RefId="3812" Id="9094" Title="..." Type="grp" Page="1">
        <Timing Type="1" Visible="0" Changeable="0">
          <Start>2025-02-05 08:40:24</Start>
          <End>2025-02-05 08:40:24</End>
        </Timing>
        <Item RefId="3845" Id="9151" Title="Test" Type="tst" Offline="1">
          <Timing.../>
        </Item>
        <Item RefId="3826" Id="9124" Title="Ankerelement..." Type="fold">
          <Timing.../>
        </Item>
        <!-- Weitere Items -->
      </Item>
    </Items>
  </exp:ExportItem>
</exp:Export>
```

**Wichtige Felder**:
- `RefId`: Referenz-ID für das Item
- `Id`: Interne ILIAS-ID
- `Title`: Angezeigter Titel
- `Type`: Typ (grp, fold, itgr, tst, file, ...)
- `Timing`: Verfügbarkeitseinschränkungen
- `Offline`: Ist das Item offline?

### Moodle Section-XML-Struktur

Die `sections/section_XXX/section.xml` hat folgende Struktur:

```xml
<section id="345">
  <number>0</number>
  <name>Kursinformationen</name>
  <summary></summary>
  <sequence>1981,1982</sequence> <!-- Activity-IDs in dieser Section -->
  <visible>1</visible>
  <timemodified>1732013647</timemodified>
</section>
```

**Wichtige Felder**:
- `id`: Section-ID
- `number`: Section-Nummer (0 = Allgemein)
- `name`: Section-Name (wichtig!)
- `sequence`: Kommaseparierte Liste von Activity-IDs

---

## 10. Zusammenfassung

**Hauptproblem**: Der aktuelle Converter erstellt eine **flache Struktur** (ein Modul pro Komponente) statt eine **hierarchische, semantische Struktur** (logische Sections mit zugeordneten Activities).

**Lösung**: 
1. Container-Struktur aus `Services/Container/export.xml` nutzen
2. ItemGroups auflösen zu ihren Items
3. Items semantisch kategorisieren (Kursinformationen, Wissensinhalt, Abschluss)
4. Moodle-Sections mit sinnvollen Namen erstellen
5. Activities korrekt zu Sections zuordnen

**Priorität**: 
- **Hoch**: Container-Parser + ItemGroup-Resolver (sonst ist die Struktur falsch)
- **Mittel**: Section-Kategorisierer (sonst sind die Namen generisch)
- **Niedrig**: Timing-Mapping (Nice-to-have)

---

**Autor**: AI Assistant  
**Letzte Aktualisierung**: 4. November 2025

