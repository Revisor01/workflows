<h1 align="center">workflows</h1>

<p align="center">
  Wiederverwendbare GitHub-Actions-Workflows für meine Repos —<br>
  einmal gepflegt, überall gleich.
</p>

<p align="center">
  <b>Deutsch</b> · <a href="README.en.md">English</a>
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
- **`docker-image.yml`** — baut ein Docker-Image und lädt es nach ghcr.io oder
  Docker Hub. In Pull Requests wird nur gebaut. Eine optionale Prüfung läuft
  gegen das fertige Image, bevor etwas hochgeladen wird.
- **`portainer-deploy.yml`** — löst den Webhook eines Portainer-Stacks aus und
  wartet auf Wunsch, bis der Dienst mit dem gebauten Commit antwortet. Fehlt
  der Webhook oder antwortet er mit einem Fehler, scheitert der Lauf.
- **`xcode-tests.yml`** — baut ein Xcode-Projekt für den Simulator und führt
  die Tests aus.
- **`xcode-cloud.yml`** — startet einen Xcode-Cloud-Workflow für den Branch
  des Laufs, wartet auf das Ende und gibt die Build-Nummer aus. Gebaut wird
  nur, wenn der Branch noch auf dem Commit des Laufs steht.

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

**Image bauen und ausrollen:**

```yaml
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: deploy
  cancel-in-progress: false

jobs:
  image:
    uses: Revisor01/workflows/.github/workflows/docker-image.yml@<sha> # 1.2.0
    permissions:
      contents: read
      packages: write
    with:
      image: ghcr.io/${{ github.repository }}

  deploy:
    needs: image
    if: github.event_name != 'pull_request'
    uses: Revisor01/workflows/.github/workflows/portainer-deploy.yml@<sha> # 1.2.0
    with:
      pruef-url: https://example.org/health
    secrets:
      webhook: ${{ secrets.PORTAINER_WEBHOOK_URL }}
```

Mehrere Images aus einem Repo: je Image ein Job mit `docker-image.yml` (oder
eine Matrix), der Deploy-Job wartet mit `needs` auf alle.

**Xcode-Tests:**

```yaml
on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  tests:
    uses: Revisor01/workflows/.github/workflows/xcode-tests.yml@<sha> # 1.2.0
    with:
      projekt: App.xcodeproj
      schema: App
      test-ziel: AppTests
```

Der Check heißt danach `tests / xcode`.

**Release über Xcode Cloud:**

```yaml
on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  bauen:
    uses: Revisor01/workflows/.github/workflows/xcode-cloud.yml@<sha> # 1.3.0
    with:
      workflow-id: <ID des Xcode-Cloud-Workflows>
    secrets:
      asc-key-id: ${{ secrets.ASC_KEY_ID }}
      asc-issuer-id: ${{ secrets.ASC_ISSUER_ID }}
      asc-key-p8: ${{ secrets.ASC_KEY_P8_BASE64 }}

  danach:
    needs: bauen
    runs-on: ubuntu-24.04
    steps:
      - run: echo "Build ${{ needs.bauen.outputs.build-nummer }}"
```

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
| `cache-pfad` | – | Ordner, der zwischen Läufen erhalten bleibt, z. B. `resources/_gen` (Hugo-Bilder) |
| `cache-dateien` | – | Muster für den Cache-Schlüssel, z. B. `assets/images/**` |
| `probe` | `false` | nur Trockenlauf |

| Secret | Für | Bedeutung |
|--------|-----|-----------|
| `ssh-key` oder `ssh-key-b64` | rsync | privater Schlüssel, roh oder base64-kodiert |
| `ssh-ziel` | rsync | `benutzer@host:pfad` |
| `ssh-known-hosts` | rsync | optional; fehlt er, wird der Host-Schlüssel abgefragt |
| `ftp-host`, `ftp-user`, `ftp-pass` | FTP | Zugang |
| `build-env` | Build | optional; Zeilen `NAME=wert`, nur im Build-Schritt gesetzt und maskiert, z. B. ein Token, das der Build zum Abrufen von Inhalten braucht |

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

## Eingaben von `docker-image.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `image` | – | Name ohne Tag, z. B. `ghcr.io/besitzer/projekt/server`; ohne Registry gilt Docker Hub |
| `kontext` | `.` | Build-Kontext |
| `dockerfile` | – | leer: `Dockerfile` im Kontext |
| `plattformen` | `linux/amd64` | mehrere durch Komma getrennt |
| `build-args` | – | Zeilen `NAME=wert` |
| `tags` | siehe unten | Regeln für [docker/metadata-action](https://github.com/docker/metadata-action#tags-input) |
| `hochladen` | `true` | `false`: nur bauen; in Pull Requests wird nie hochgeladen |
| `node-version` | – | Node für die Vorbereitung |
| `vorbereitung` | – | Befehl vor dem Build, z. B. ein Frontend bauen |
| `pruefung` | – | Befehl gegen das gebaute Image (Name in `$PRUEFLING`); scheitert er, wird nichts hochgeladen |
| `registry-benutzer` | – | leer bei ghcr.io: der auslösende Benutzer |

| Secret | Bedeutung |
|--------|-----------|
| `registry-token` | leer bei ghcr.io: `GITHUB_TOKEN` des Aufrufers; für Docker Hub ein Zugriffstoken |

Ohne `tags` bekommt das Image `latest` (nur auf dem Standard-Branch),
`sha-<commit>` und bei einem Versions-Tag `1.2.3` und `1.2`. Der Build-Cache
liegt je Image im Cache von GitHub Actions. Für ghcr.io braucht der Job
`packages: write`.

## Eingaben von `portainer-deploy.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `pruef-url` | – | Adresse, die danach antworten muss; leer: keine Prüfung |
| `pruef-status` | `200` | erlaubte HTTP-Status, durch Leerzeichen getrennt |
| `revision-feld` | – | jq-Pfad in der JSON-Antwort, der den gebauten Commit enthalten muss, z. B. `.revision` |
| `wartezeit` | `300` | Sekunden, die die Prüfung höchstens wartet |

Das Secret `webhook` ist Pflicht. Webhook-Adressen gehören immer in ein Secret:
Wer sie kennt, kann den Stack neu ausrollen, und Variablen erscheinen im Log im
Klartext.

## Eingaben von `xcode-tests.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `projekt` | – | `.xcodeproj` oder `.xcworkspace` |
| `schema` | – | Scheme |
| `aktion` | `test` | `test` oder `build` |
| `test-ziel` | – | nur dieses Test-Target (`-only-testing`) |
| `runner` | `macos-26` | Runner-Image |
| `xcode` | `neuestes` | `neuestes` (stabiles Xcode des Runners), `vorgabe` (nicht wechseln) oder Pfad zur `Xcode.app` |
| `ohne-signierung` | `false` | ohne Signierung bauen |
| `vorbereitung` | – | Befehl vor dem Build, z. B. ein Platzhalter für eine Datei, die nicht im Repo liegt |
| `artefakt` | – | Datei, die danach als Artefakt bereitsteht, z. B. `Package.resolved` |
| `timeout` | `40` | Minuten |

Getestet wird auf dem neuesten iPhone-Simulator des Runners. Schlägt der Lauf
fehl, steht das vollständige Log als Artefakt `xcode-log` bereit.

## Eingaben von `xcode-cloud.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `workflow-id` | – | ID des Xcode-Cloud-Workflows (App Store Connect API, `ciWorkflows`) |
| `wartezeit` | `60` | Minuten, die auf das Ende gewartet wird (höchstens 100) |

Secrets: `asc-key-id`, `asc-issuer-id` und `asc-key-p8`, der private Schlüssel
eines App-Store-Connect-API-Schlüssels, base64-kodiert. Ausgabe: `build-nummer`.

Xcode Cloud baut immer den aktuellen Stand eines Branches, nicht einen
bestimmten Commit. Steht der Branch beim Start schon weiter, startet der
Baustein nichts. Hat Xcode Cloud trotzdem einen anderen Commit gebaut, scheitert
der Lauf. Den Upload nach TestFlight und die Testgruppen legt der Xcode-Cloud-
Workflow selbst fest.

## Versionen

Was sich wann geändert hat, steht in [CHANGELOG.md](CHANGELOG.md) — nach
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/). Die
[Releases](https://github.com/Revisor01/workflows/releases) fassen jede Version
zusammen.

## Mitmachen

Fehlermeldungen und Vorschläge sind willkommen — gern als
[Issue](https://github.com/Revisor01/workflows/issues). Sicherheitslücken bitte
vertraulich melden, wie in [SECURITY.md](SECURITY.md) beschrieben. Pull
Requests laufen durch actionlint und einen Secret-Scan; siehe
[CONTRIBUTING.md](CONTRIBUTING.md).

## Lizenz

[MIT](LICENSE) © 2026 Simon Luthe

## Kontakt

Pastor Simon Luthe · [mail@simonluthe.de](mailto:mail@simonluthe.de) ·
[simonluthe.de](https://simonluthe.de)
