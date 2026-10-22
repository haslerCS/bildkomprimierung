# Bildkomprimierung für Codex

Ein Codex-Skill zur lokalen Optimierung vorhandener JPEG-, PNG- und WebP-Bilder in Webprojekten. Er erstellt passende responsive Varianten, prüft Dateigrößen und unterstützt bei der sicheren Einbindung in den Quellcode. Die Originalbilder bleiben erhalten.

## Installation

```bash
git clone https://github.com/haslerCS/bildkomprimierung.git ~/.codex/skills/bildkomprimierung
```

Alternativ kann das Repository über **Code → Download ZIP** heruntergeladen und als Ordner `bildkomprimierung` unter `~/.codex/skills/` entpackt werden. Starte Codex nach der Installation neu, damit der Skill erkannt wird.

## Nutzung

Rufe den Skill ausdrücklich auf und nenne den Bildordner innerhalb des Webprojekts, zum Beispiel:

> Verwende den Skill `bildkomprimierung` für `public/images` in diesem Webprojekt.

Der Skill untersucht Bildverwendungen, bereitet Varianten lokal vor, bindet geeignete Varianten ein und prüft das Ergebnis. Ohne ausdrücklich genannten Bildordner fragt er nach dem Pfad.

## Voraussetzungen

- Python 3 und [Pillow](https://pypi.org/project/pillow/) gemäß [`scripts/requirements.txt`](scripts/requirements.txt)
- [ExifTool](https://exiftool.org/) im `PATH`
- Für die Prüfung der Einbindung die Build- und Browserwerkzeuge des jeweiligen Webprojekts

Die Python-Abhängigkeit lässt sich isoliert installieren:

```bash
python3 -m venv /tmp/bildkomprimierung-venv
/tmp/bildkomprimierung-venv/bin/python -m pip install -r ~/.codex/skills/bildkomprimierung/scripts/requirements.txt
```

Die vollständige Arbeitsanweisung steht in [`SKILL.md`](SKILL.md). Der vorbereitende Bild-Helper liegt in [`scripts/prepare_images.py`](scripts/prepare_images.py); Hinweise zur Einbindung stehen in [`references/integration.md`](references/integration.md).
