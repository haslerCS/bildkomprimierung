---
name: bildkomprimierung
description: Optimiere auf ausdrücklichen Auftrag vorhandene JPEG-, PNG- und WebP-Bilder in einem gewählten Webprojektordner, erstelle responsive Varianten und passe verwendete Bildverweise im Quellcode an.
---

# Bilder für Websites optimieren

Starte nur, wenn der Nutzer diesen Skill ausdrücklich aufruft oder die Optimierung eines Bildordners ausdrücklich verlangt. Ist kein Ordner genannt, frage nach ihm. Bearbeite den Ordner rekursiv innerhalb des Webprojekts. Beschaffe oder erzeuge keine neuen Bildmotive und lade keine Bilder zu Online-Diensten hoch.

## Ergebnis

- Bearbeite statische JPEG-, PNG- und WebP-Dateien im gewählten Ordner, auch wenn sie derzeit ungenutzt sind. Überspringe SVG, GIF und alle animierten Bilder mit begründetem Bericht.
- Erhalte jedes Original unverändert. Lege Varianten mit eindeutigen, wiederholbaren Namen daneben ab. Erhalte Seitenverhältnis, Ausrichtung, Farbdarstellung und Copyright-Angaben; entferne GPS- und unnötige Kameradaten. Schneide Bilder nicht zu und vergrößere sie nicht.
- Für ungenutzte Bilder: Breiten 320, 640, 960, 1280 und 1920 Pixel, begrenzt auf die Originalbreite, sowie die Originalbreite. Erzeuge auch passende JPEG-/PNG-Größenvarianten. Füge ungenutzte Bilder nirgends im Quellcode ein.
- Für verwendete Bilder: leite benötigte Breiten aus der tatsächlichen Darstellung ab, einschließlich dichter Displays bis zur Originalauflösung. Nutze keine pauschalen Varianten, wenn die Verwendung bekannt ist. Kannst du die Anzeigegröße nicht zuverlässig ermitteln, führe nur sichere Optimierungen aus und melde die offene Einbindung.
- Verwende eine WebP-Variante nur, wenn sie mindestens 10 % kleiner als die entsprechende JPEG-/PNG-Variante gleicher Abmessungen ist. Ist WebP nicht vorteilhaft, können kleinere JPEG-/PNG-Varianten weiterhin eingebunden werden. Bei vorhandenem WebP sind kleinere WebP-Größenvarianten möglich. Übernimm nur Varianten, die gegenüber dem bisher geladenen Bild Übertragungsgröße sparen.
- Erhalte das sichtbare Layout und die Bildschärfe. Bei Fotos ist eine im normalen Gebrauch kaum sichtbare Abweichung zulässig; bei Logos, Screenshots und Textgrafiken bewahre scharfe Kanten. Prüfe kritische Bilder visuell.

## Ablauf

1. Ermittle Projektwurzel, gewählten Ordner, Git-Status, Bildverwendungen und vorhandene Bildpipeline. Erfasse vorhandene Build-/Browserfehler als Ausgangszustand. Folge keinen Symlinks außerhalb des gewählten Ordners. Berühre keine Dateien anderer Bildläufe oder Nutzeränderungen.
2. Erzeuge Bildkandidaten lokal im temporären Staging-Bereich mit [`scripts/prepare_images.py`](scripts/prepare_images.py). Installiere fehlende lokale Werkzeuge bei Bedarf isoliert für diesen Skill, ohne die Paketkonfiguration des Webprojekts zu ändern. Pillow und ExifTool werden benötigt. Die CLI liefert einen JSON-Plan mit Größen, Dateigrößen und ausgelassenen Varianten. Für verwendete Bilder kann eine `--width-map` pro Quelldatei übergeben werden; ohne Eintrag gelten die Breiten für ungenutzte Bilder. Nutze bei Bedarf `--kind-map`, um PNG-Fotos verlustbehaftet oder JPEG-/WebP-Textgrafiken verlustfrei als WebP zu kodieren; Standard ist PNG = Grafik, JPEG/WebP = Foto. Prüfe verlustbehaftete Kandidaten visuell, besonders bei Vollgröße und Textkanten.
3. Vergleiche Kandidaten mit den jeweils passenden Dateien, prüfe Aussehen, Transparenz, Metadaten und Dateigrößen. Kopiere nur ausgewählte Kandidaten neben die Originale. Halte die eigenen Ausgaben in `.bildkomprimierung-manifest.json` an der Projektwurzel fest, damit ein erneuter Lauf sie aktualisieren und nach erfolgreicher Validierung veraltete eigene Varianten entfernen kann. Verwechsle ähnlich benannte fremde Dateien nicht mit eigenen Ausgaben. Behandle vom Helper ausgelassene Quelldateien einzeln mit einem sicheren lokalen Verfahren oder berichte, warum sie nicht verarbeitet werden konnten.
4. Passe nur tatsächlich verwendete Bildverweise an. Lies dazu [`references/integration.md`](references/integration.md). Berücksichtige HTML, CSS und die tatsächlich verwendeten Komponenten/Frameworks. Erhalte vorhandene Framework-Bildoptimierung und ergänze nur nachweisbare Lücken. Ergänze responsive Quellen, `sizes`, intrinsische `width`/`height` und passende Ladehinweise, wenn die Darstellung zuverlässig erkennbar ist. Behalte JPEG-/PNG-Fallbacks. Dynamische oder mehrdeutige Verweise nicht erraten; im Bericht aufführen.
5. Prüfe Build und, wenn lokal startbar, die betroffenen Seiten im Browser bei mehreren Viewports. Prüfe geladene Bild-URLs, Abmessungen, sichtbares Layout und tatsächliche Übertragungsgrößen. Wenn der Build oder die Bilddarstellung durch die Änderungen beschädigt wird, stelle ausschließlich die Änderungen dieses Laufs wieder her und melde den Fehler. Ist kein Browserstart möglich, stütze die Entscheidung auf Dateigrößen, Abmessungen und Quellcodeprüfung und kennzeichne die fehlende Browserprüfung.
6. Berichte pro Bild Originalgröße, erzeugte/eingebundene Varianten, Einsparung, geänderte Quellcode-Stellen und Gründe für ausgelassene Bilder. Entferne erst nach erfolgreicher Prüfung nicht mehr benötigte, eindeutig eigene Varianten.

Beispiel für die Bildvorbereitung (Pfade an das Projekt anpassen):

```bash
python3 -m venv /tmp/bildkomprimierung-venv
/tmp/bildkomprimierung-venv/bin/python -m pip install -r scripts/requirements.txt
/tmp/bildkomprimierung-venv/bin/python scripts/prepare_images.py \
  --project-root /pfad/zum/webprojekt \
  --folder /pfad/zum/webprojekt/public/images \
  --staging /tmp/bildkomprimierung-staging \
  --plan /tmp/bildkomprimierung-plan.json
```

Die Vorbereitung ändert das Webprojekt nicht. Führe Einbindung, Validierung und Aufräumen anschließend anhand des Plans durch.
