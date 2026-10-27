# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.

Das Format orientiert sich an [Keep a Changelog 1.1.0](https://keepachangelog.com/de/1.1.0/),
die Versionierung folgt [SemVer 2.0.0](https://semver.org/lang/de/).

## [Unreleased]

### Sonstiges

- README, Vorlagen und Hinweise gibt es nur noch auf Deutsch.

## [1.4.0] - 2026-10-26

### Hinzugefügt

- `play-upload.yml`: lädt ein signiertes Android-App-Bundle aus einem Artefakt zu Google Play und gibt es für die gewählten Tracks frei; `production` geht gestaffelt raus, Eingaben und Neuigkeiten werden vorher geprüft, auf Wunsch schon vor dem Bau, und ein Dry-Run veröffentlicht nichts.

## [1.3.1] - 2026-10-26

### Geändert

- `xcode-tests.yml`: Die Zusammenfassung nennt die Zahl der Compiler-Warnungen aus eigenen Dateien und listet sie auf; die ersten 20 erscheinen als Anmerkung am Code.

## [1.3.0] - 2026-10-26

### Hinzugefügt

- `xcode-cloud.yml`: startet einen Xcode-Cloud-Workflow für den Branch des Laufs, wartet auf das Ende und gibt die Build-Nummer aus; gebaut wird nur der Commit, für den der Lauf gestartet wurde.

## [1.2.0] - 2026-10-26

### Hinzugefügt

- `docker-image.yml`: baut ein Docker-Image, prüft es auf Wunsch und lädt es nach ghcr.io oder Docker Hub; in Pull Requests wird nur gebaut.
- `portainer-deploy.yml`: rollt einen Portainer-Stack per Webhook aus und wartet auf Wunsch, bis der Dienst mit dem neuen Stand antwortet; ein fehlender oder abgelehnter Webhook lässt den Lauf scheitern.
- `xcode-tests.yml`: baut ein Xcode-Projekt für den Simulator und führt die Tests aus.

### Sonstiges

- README, Vorlagen für Issues und Pull Requests sowie die Hinweise zu Sicherheit und Mitmachen gibt es jetzt auch auf Englisch.

## [1.1.1] - 2026-10-26

### Behoben

- `website.yml`: Ein mehrzeiliger `build-befehl` bricht den Lauf nicht mehr gleich beim Prüfen der Eingaben ab.

## [1.1.0] - 2026-10-26

### Hinzugefügt

- `website.yml`: Secret `build-env` mit Zeilen `NAME=wert`, die nur der Build-Schritt als Umgebung bekommt (z. B. ein Token zum Abrufen von Terminen); jeder Wert wird im Log maskiert.
- `website.yml`: `cache-pfad` und `cache-dateien` erhalten einen Ordner zwischen Läufen, etwa die von Hugo gerechneten Bilder.

## [1.0.2] - 2026-10-26

### Behoben

- FTP: Der Trockenlauf zählt Übertragungen richtig und bricht ab, wenn Anmeldung oder Zielordner fehlschlagen, statt leer und harmlos auszusehen.
- FTP: Passwörter mit Sonderzeichen funktionieren; das Passwort steht in keiner Datei mehr.
- rsync: Dateien, bei denen nur die Zeit abweicht, zählen nicht mehr als geändert.

### Sicherheit

- Zeilen des FTP-Trockenlaufs erscheinen ohne Anmeldedaten im Log.
- Ein gelöschter Ordner zählt für die Löschsperre zehnfach.

## [1.0.1] - 2026-10-26

### Behoben

- Ohne Generator werden `.git/` und `.github/` auch per FTP sicher ausgelassen.

### Geändert

- Der Trockenlauf zeigt seine ersten Zeilen, damit sich die Zählung nachvollziehen lässt.

## [1.0.0] - 2026-10-26

### Hinzugefügt

- Baustein `website.yml`: Website ohne Generator, mit Hugo oder mit npm bauen
  und per rsync über SSH oder per FTP übertragen. Jeder Lauf beginnt mit einem
  Trockenlauf; zu viele Löschungen brechen ab, bevor etwas geändert wird.
- Baustein `secret-scan.yml`: gitleaks über neue Commits sowie Titel und
  Beschreibung eines Pull Requests.

[Unreleased]: https://github.com/Revisor01/workflows/compare/1.4.0...HEAD
[1.4.0]: https://github.com/Revisor01/workflows/compare/1.3.1...1.4.0
[1.3.1]: https://github.com/Revisor01/workflows/compare/1.3.0...1.3.1
[1.3.0]: https://github.com/Revisor01/workflows/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/Revisor01/workflows/compare/1.1.1...1.2.0
[1.1.1]: https://github.com/Revisor01/workflows/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/Revisor01/workflows/compare/1.0.2...1.1.0
[1.0.2]: https://github.com/Revisor01/workflows/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/Revisor01/workflows/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/Revisor01/workflows/releases/tag/1.0.0
