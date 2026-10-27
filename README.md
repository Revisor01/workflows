<h1 align="center">workflows</h1>

<p align="center">
  Wiederverwendbare GitHub-Actions-Workflows für meine Repos —<br>
  einmal gepflegt, überall gleich.
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/Revisor01/workflows" alt="Lizenz">
</p>

## Worum es geht

Gemeinsame Abläufe meiner Repos an einer Stelle. Ziele und Zugangsdaten
bleiben als Secrets im aufrufenden Repo.

## Bausteine

- **`website.yml`**: Website bauen (ohne Generator, Hugo, npm) und per rsync
  oder FTP übertragen, mit Trockenlauf und Löschgrenze.
- **`secret-scan.yml`**: Commits und PR-Texte mit
  [gitleaks](https://github.com/gitleaks/gitleaks) prüfen.
- **`docker-image.yml`**: Docker-Image bauen, prüfen und hochladen.
- **`portainer-deploy.yml`**: Portainer-Webhook auslösen und auf den Dienst
  warten.
- **`xcode-tests.yml`**: Xcode-Projekt für den Simulator bauen und testen.
- **`xcode-cloud.yml`**: Xcode-Cloud-Workflow starten und auf die
  Build-Nummer warten.
- **`play-upload.yml`**: Android-App-Bundle zu Google Play hochladen.

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

**Android-Release zu Google Play:**

```yaml
on:
  workflow_dispatch:
    inputs:
      tracks:
        default: internal
      dry_run:
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  pruefen:
    uses: Revisor01/workflows/.github/workflows/play-upload.yml@<sha> # 1.4.0
    with:
      paket: de.example.app
      tracks: ${{ inputs.tracks }}
      release-notes-datei: release-notes-de.txt
      nur-pruefen: true

  bauen:
    needs: pruefen
    runs-on: ubuntu-24.04
    timeout-minutes: 60
    steps:
      # signiertes AAB bauen, beim Dry-Run mit angehobenem versionCode
      - uses: actions/upload-artifact@<sha> # v7.0.2
        with:
          name: aab
          path: android/app/build/outputs/bundle/release/app-release.aab
          retention-days: 1

  hochladen:
    needs: bauen
    uses: Revisor01/workflows/.github/workflows/play-upload.yml@<sha> # 1.4.0
    with:
      paket: de.example.app
      tracks: ${{ inputs.tracks }}
      artefakt: aab
      release-notes-datei: release-notes-de.txt
      dry-run: ${{ inputs.dry_run }}
    secrets:
      dienstkonto: ${{ secrets.GPLAY_SA_JSON_BASE64 }}
```

Bauen bleibt im aufrufenden Repo. Der Schlüssel des Dienstkontos kommt nur in
den Upload-Job, nicht in den Job, der npm und Gradle ausführt. Ausgabe:
`version-code`.

## Eingaben von `website.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `generator` | `keiner` | `keiner`, `hugo` oder `npm` |
| `hugo-version` | `0.164.0` | Hugo (extended) |
| `node-version` | `26` | Node für `npm` |
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
eines App-Store-Connect-API-Schlüssels, base64-kodiert. Ausgabe: `build-nummer`. Der fertige Build wird allen internen TestFlight-Gruppen der App zugeordnet.

Xcode Cloud baut immer den aktuellen Stand eines Branches, nicht einen
bestimmten Commit. Steht der Branch beim Start schon weiter, startet der
Baustein nichts. Hat Xcode Cloud trotzdem einen anderen Commit gebaut, scheitert
der Lauf. Den Upload nach TestFlight und die Testgruppen legt der Xcode-Cloud-
Workflow selbst fest.

## Eingaben von `play-upload.yml`

| Eingabe | Standard | Bedeutung |
|---------|----------|-----------|
| `paket` | – | Paketname bei Google Play |
| `tracks` | – | kommagetrennt aus `internal`, `alpha`, `beta`, `production`; Leerzeichen und doppelte Namen stören nicht, unbekannte brechen ab |
| `artefakt` | – | Artefakt mit genau einer `.aab`-Datei |
| `status` | `completed` | `completed` gibt sofort frei, `draft` legt einen Entwurf in der Play Console an (der einzige Status, solange die App nie veröffentlicht war) |
| `production-anteil` | `0.1` | nur `production` mit `completed`: Anteil der Nutzer:innen, die das Update zuerst bekommen; `1` = alle |
| `release-notes` | – | Neuigkeiten als Text |
| `release-notes-datei` | – | Neuigkeiten aus einer Datei im Repo |
| `sprache` | `de-DE` | Sprache der Neuigkeiten |
| `dry-run` | `false` | hochladen, Tracks setzen und prüfen, dann verwerfen |
| `nur-pruefen` | `false` | nur Eingaben und Neuigkeiten prüfen, ohne Netz und ohne Schlüssel |

Das Secret `dienstkonto` ist der JSON-Schlüssel eines Google-Dienstkontos,
base64-kodiert; bei `nur-pruefen` wird es nicht gebraucht.

Neuigkeiten über 500 Zeichen brechen ab, bevor eine Bearbeitung angelegt wird;
Google ließe sie sonst erst beim Übernehmen scheitern, mit einer Meldung, die
nach fehlenden Rechten aussieht. Antworten mit 5xx und Verbindungsfehler werden
bis zu dreimal wiederholt. Scheitert ein Schritt, wird die Bearbeitung
verworfen. Ein Dry-Run verbraucht keinen `versionCode`, Google lehnt beim
Hochladen aber einen schon vergebenen ab; der Aufrufer baut dafür mit einer
höheren Nummer.

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
