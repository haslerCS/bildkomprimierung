# Bildvarianten sicher einbinden

Lies diese Referenz nur für tatsächlich im Projekt verwendete Bilder. Die Staging-Dateien aus dem JSON-Plan sind noch nicht eingebunden.

## Verwendungen erfassen

Suche die ausgewählten Quellpfade in HTML, CSS, JS/TS, JSX/TSX, Vue, Svelte, Astro, MD/MDX, Templates und Datenkonfigurationen, soweit diese Dateitypen im Projekt vorkommen. Prüfe importierte Assets, öffentliche URLs und zur Laufzeit zusammengesetzte Pfade. Ändere nur eindeutige Verweise. Gib mehrdeutige oder dynamische Fälle als offene Punkte aus. Ein Bild kann an mehreren Stellen mit unterschiedlichen Anzeigegrößen verwendet werden; vereinige dafür nur die benötigten Breiten.

Wenn ein Framework oder CDN bereits automatisch moderne Formate, responsive Varianten und Caching liefert, nutze dessen Bildkomponente weiter. Prüfe, ob die neuen Dateien dort überhaupt einen Vorteil bringen, bevor du Pfade ersetzt. Ersetze keine Bildkomponente durch ein einfaches `<img>`.

## HTML und Komponenten

Für JPEG/PNG mit ausreichend kleinerem WebP ist `<picture>` mit WebP-`<source>` und JPEG-/PNG-`<img>`-Fallback geeignet. Nutze passende `srcset`-Breiten für beide Formate und ein aus Layoutregeln abgeleitetes `sizes`. Für vorhandenes WebP oder ohne lohnendes WebP reicht `srcset` am bestehenden Bild-/Framework-Element. Browser sollen pro Bild nur eine Variante laden. Behalte `alt`, Klassen, Semantik, Event-Handler und andere vorhandene Attribute.

Trage `width` und `height` im Original-Seitenverhältnis ein, sofern sie fehlen. Prüfe vorhandene CSS-Regeln, damit die sichtbare Größe gleich bleibt. Wähle `sizes` aus der tatsächlichen maximalen CSS-Breite je Viewport. Nutze 1x- und 2x-Kandidaten nur soweit die Originalauflösung reicht; keine künstliche Vergrößerung.

Setze `loading="lazy"` nur für sicher außerhalb des anfänglichen Viewports liegende Bilder. Hero-/LCP-Bilder sollen früh laden; setze dort bei Bedarf `fetchpriority="high"` oder ein passendes Framework-Äquivalent. Verändere bestehende Ladehinweise nur, wenn ihre Wirkung nachprüfbar besser ist.

## CSS-Bilder

Bei `background-image` oder verwandten Eigenschaften prüfe, ob `image-set()` mit Auflösungs-/Formatvarianten und einem Original-Fallback im konkreten Browserziel sinnvoll ist. Bewahre Reihenfolge, Layer, Position und Layout. Wenn die CSS-Einbindung oder Unterstützung nicht sicher ist, behalte den bestehenden Verweis und berichte die bereitgestellten Varianten. Kopiere keine HTML-Attribute in CSS.

## Prüfung und Wiederholung

Vergleiche die tatsächlich übertragene Datei je Viewport mit der bisherigen Einbindung. Prüfe, dass kein Browser beide Fallback- und WebP-Dateien lädt. Öffne betroffene Seiten visuell; achte besonders auf Transparenz, Textschärfe, Farbverschiebung, Bildausschnitt und Layoutsprünge. Bei fehlendem Browserzugang prüfe Build, Pfadauflösung und generierte Dateien statisch und kennzeichne die Grenze.

Speichere in `.bildkomprimierung-manifest.json` an der Projektwurzel mindestens Quellpfad, Hash der Quelle, eigene Ausgabepfade, verwendete Breiten und die berührten Quellcodepfade. Beim nächsten Lauf überschreibe oder entferne nur dort aufgeführte eigene Ausgaben. Der Helper meldet namensähnliche Dateien außerhalb des Manifests ausdrücklich zur Prüfung. Für einen Rollback sichere vor dem Editieren die betroffenen Quellcode-Dateien und eventuell vorhandene eigene Varianten außerhalb des Projekts; stelle bei einem durch diesen Lauf verursachten Fehler nur diese Dateien wieder her.
