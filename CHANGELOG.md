# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.

Das Format orientiert sich an [Keep a Changelog 1.1.0](https://keepachangelog.com/de/1.1.0/),
die Versionierung folgt [SemVer 2.0.0](https://semver.org/lang/de/).

## [Unreleased]

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

[Unreleased]: https://github.com/Revisor01/workflows/compare/1.0.1...HEAD
[1.0.1]: https://github.com/Revisor01/workflows/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/Revisor01/workflows/releases/tag/1.0.0
