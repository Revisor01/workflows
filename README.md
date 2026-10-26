<h1 align="center">workflows</h1>

<p align="center">
  Wiederverwendbare GitHub-Actions-Workflows für meine Repos —<br>
  einmal gepflegt, überall gleich.
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/Revisor01/workflows" alt="Lizenz">
</p>

## Worum es geht

Viele meiner Repos brauchen dieselben Abläufe: eine Website bauen und
hochladen, jeden Commit auf Zugangsdaten prüfen. Statt in jedem Repo eine
eigene Fassung zu pflegen, rufen sie die Bausteine aus diesem Repo auf. Ziele
und Zugangsdaten bleiben als Secrets im aufrufenden Repo; hier steht nichts
davon.

## Bausteine

- **`website.yml`** — baut eine Website ohne Generator, mit Hugo oder mit npm
  und überträgt sie per rsync über SSH oder per FTP. Jeder Lauf beginnt mit
  einem Trockenlauf, der zeigt, wie viele Dateien neu, geändert oder zu löschen
  sind. Mehr Löschungen als erlaubt brechen ab, bevor etwas geändert wird.
- **`secret-scan.yml`** — prüft neue Commits sowie Titel und Beschreibung
  eines Pull Requests mit [gitleaks](https://github.com/gitleaks/gitleaks).
  Von Hand gestartet prüft er die ganze Historie.

## Aufruf

Bausteine werden immer über den Commit-SHA eines Releases eingebunden, nicht
über einen Branch oder Tag. Dependabot hält den SHA aktuell, wenn im
aufrufenden Repo `github-actions` als Ökosystem eingetragen ist.

**Hugo-Website per rsync:**

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      probe:
        description: "Nur Trockenlauf"
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  website:
    uses: Revisor01/workflows/.github/workflows/website.yml@<sha> # 1.0.0
    with:
      generator: hugo
      probe: ${{ inputs.probe == true }}
    secrets:
      ssh-key: ${{ secrets.DEPLOY_SSH_KEY }}
      ssh-ziel: ${{ secrets.DEPLOY_ZIEL }}
```

**Statische Seite per FTP, ohne Löschen am Ziel:**

```yaml
jobs:
  website:
    uses: Revisor01/workflows/.github/workflows/website.yml@<sha> # 1.0.0
    with:
      uebertragung: ftp
      ftp-pfad: /
      loeschen: false
      ausschluesse: |
        README.md
        CHANGELOG.md
    secrets:
      ftp-host: ${{ secrets.FTP_HOST }}
      ftp-user: ${{ secrets.FTP_USER }}
      ftp-pass: ${{ secrets.FTP_PASS }}
```

**Secret-Scan:**

```yaml
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, edited, synchronize, reopened]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  scan:
    uses: Revisor01/workflows/.github/workflows/secret-scan.yml@<sha> # 1.0.0
    secrets:
      GITLEAKS_EXTRA_RULES: ${{ secrets.GITLEAKS_EXTRA_RULES }}
```

Der Check heißt danach `scan / scan`; ein Branch-Schutz muss diesen Namen
verlangen.

## Eingaben von `website.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `generator` | `keiner` | `keiner`, `hugo` oder `npm` |
| `hugo-version` | `0.164.0` | Hugo (extended) |
| `node-version` | `22` | Node für `npm` |
| `build-befehl` | je Generator | leer: `hugo --minify --gc` bzw. `npm ci && npm run build` |
| `ausgabe` | je Generator | übertragener Ordner: `.`, `public` bzw. `dist` |
| `ausschluesse` | – | Muster, die nicht übertragen werden, eines je Zeile; Ordner mit `/` am Ende; ohne Generator sind `.git/` und `.github/` immer ausgeschlossen |
| `uebertragung` | `rsync` | `rsync` oder `ftp` |
| `rsync-optionen` | – | zusätzliche Optionen, z. B. `--checksum` |
| `ftp-pfad` | `/` | Zielordner auf dem FTP-Server |
| `ftp-tls-erzwingen` | `false` | nur verschlüsselt verbinden |
| `ftp-tls-pruefen` | `false` | Zertifikat des FTP-Servers prüfen |
| `loeschen` | `true` | am Ziel löschen, was es in der Ausgabe nicht mehr gibt |
| `max-loeschungen` | `50` | mehr Löschungen brechen ab, auch im echten Lauf |
| `probe` | `false` | nur Trockenlauf |

| Secret | Für | Bedeutung |
|--------|-----|-----------|
| `ssh-key` oder `ssh-key-b64` | rsync | privater Schlüssel, roh oder base64-kodiert |
| `ssh-ziel` | rsync | `benutzer@host:pfad` |
| `ssh-known-hosts` | rsync | optional; fehlt er, wird der Host-Schlüssel abgefragt |
| `ftp-host`, `ftp-user`, `ftp-pass` | FTP | Zugang |

Am Ziel ausgeschlossene Dateien bleiben bei `loeschen: true` stehen; so lassen
sich Ordner wie `.well-known/` schützen.

Zum Trockenlauf: Als geändert zählt eine Datei, deren Inhalt oder Größe
abweicht; nur eine andere Zeit zählt nicht. Per FTP prüft der Lauf vorab
Anmeldung und Zielordner und bricht ab, wenn eins davon fehlt. Ein dort
gelöschter Ordner zählt für die Löschsperre zehnfach, weil lftp nicht sagt, wie
viele Dateien darin liegen.

## Eingaben von `secret-scan.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `konfiguration` | `.gitleaks.toml` | gitleaks-Konfiguration im aufrufenden Repo |

Das optionale Secret `GITLEAKS_EXTRA_RULES` hängt weitere Regeln an, die nicht
im Repo stehen sollen.

## Versionen

Was sich wann geändert hat, steht in [CHANGELOG.md](CHANGELOG.md) — nach
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/). Die
[Releases](https://github.com/Revisor01/workflows/releases) fassen jede Version
zusammen.

## Mitmachen

Fehlermeldungen und Vorschläge sind willkommen — gern als
[Issue](https://github.com/Revisor01/workflows/issues). Sicherheitslücken bitte
vertraulich melden, wie in [SECURITY.md](SECURITY.md) beschrieben. Pull
Requests laufen durch actionlint und einen Secret-Scan; die Grundsätze für
Beiträge stehen in [CLAUDE.md](CLAUDE.md).

## Lizenz

[MIT](LICENSE) © 2026 Simon Luthe

## Kontakt

Pastor Simon Luthe · [mail@simonluthe.de](mailto:mail@simonluthe.de) ·
[simonluthe.de](https://simonluthe.de)
