<h1 align="center">workflows</h1>

<p align="center">
  Reusable GitHub Actions workflows for my repositories —<br>
  maintained once, the same everywhere.
</p>

<p align="center">
  <a href="README.md">Deutsch</a> · <b>English</b>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/Revisor01/workflows" alt="License">
</p>

## What it is about

Many of my repositories need the same steps: build and upload a website, check
every commit for credentials. Instead of maintaining a separate copy in each
repository, they call the building blocks from this one. Targets and
credentials stay as secrets in the calling repository; none of them are here.

The input names are German; their meaning is explained in the tables below.

## Building blocks

- **`website.yml`** — builds a website without a generator, with Hugo or with
  npm, and uploads it via rsync over SSH or via FTP. Every run starts with a
  dry run that shows how many files are new, changed or to be deleted. More
  deletions than allowed abort the run before anything is changed.
- **`secret-scan.yml`** — checks new commits as well as the title and
  description of a pull request with [gitleaks](https://github.com/gitleaks/gitleaks).
  Started by hand, it checks the whole history.
- **`docker-image.yml`** — builds a Docker image and pushes it to ghcr.io or
  Docker Hub. Pull requests only build. An optional check runs against the
  finished image before anything is pushed.
- **`portainer-deploy.yml`** — triggers the webhook of a Portainer stack and
  optionally waits until the service answers with the built commit. A missing
  webhook or an error response fails the run.
- **`xcode-tests.yml`** — builds an Xcode project for the simulator and runs
  the tests.
- **`xcode-cloud.yml`** — starts an Xcode Cloud workflow for the run's branch,
  waits for it to finish and returns the build number. It only builds if the
  branch is still on the run's commit.
- **`play-upload.yml`** — uploads a signed Android App Bundle from an artifact
  to Google Play and releases it to one or more tracks; `production` is rolled
  out in stages. Inputs and release notes are checked first, optionally before
  the build. A dry run uploads and validates without publishing anything.

## Usage

Building blocks are always referenced by the commit SHA of a release, not by a
branch or tag. Dependabot keeps the SHA up to date if `github-actions` is
listed as an ecosystem in the calling repository.

**Hugo website via rsync:**

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      probe:
        description: "Dry run only"
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

**Static site via FTP, without deleting at the target:**

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

**Secret scan:**

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

The check is then called `scan / scan`; branch protection has to require that
name.

**Build and deploy an image:**

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

Several images from one repository: one job with `docker-image.yml` per image
(or a matrix); the deploy job waits for all of them with `needs`.

**Xcode tests:**

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

The check is then called `tests / xcode`.

**Release via Xcode Cloud:**

```yaml
on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  bauen:
    uses: Revisor01/workflows/.github/workflows/xcode-cloud.yml@<sha> # 1.3.0
    with:
      workflow-id: <Xcode Cloud workflow ID>
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

**Android release to Google Play:**

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
      # build the signed AAB, with a raised versionCode for a dry run
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

Building stays in the calling repository. The service account key only reaches
the upload job, not the job that runs npm and Gradle. Output: `version-code`.

## Inputs of `website.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `generator` | `keiner` | `keiner` (none), `hugo` or `npm` |
| `hugo-version` | `0.164.0` | Hugo (extended) |
| `node-version` | `22` | Node for `npm` |
| `build-befehl` | per generator | build command; empty: `hugo --minify --gc` or `npm ci && npm run build` |
| `ausgabe` | per generator | folder to upload: `.`, `public` or `dist` |
| `ausschluesse` | – | patterns not to upload, one per line; folders end with `/`; without a generator `.git/` and `.github/` are always excluded |
| `uebertragung` | `rsync` | transfer: `rsync` or `ftp` |
| `rsync-optionen` | – | additional options, e.g. `--checksum` |
| `ftp-pfad` | `/` | target folder on the FTP server |
| `ftp-tls-erzwingen` | `false` | connect encrypted only |
| `ftp-tls-pruefen` | `false` | verify the FTP server's certificate |
| `loeschen` | `true` | delete at the target what no longer exists in the output |
| `max-loeschungen` | `50` | more deletions abort, in the real run too |
| `cache-pfad` | – | folder kept between runs, e.g. `resources/_gen` (Hugo images) |
| `cache-dateien` | – | patterns for the cache key, e.g. `assets/images/**` |
| `probe` | `false` | dry run only |

| Secret | For | Meaning |
|--------|-----|---------|
| `ssh-key` or `ssh-key-b64` | rsync | private key, raw or base64-encoded |
| `ssh-ziel` | rsync | `user@host:path` |
| `ssh-known-hosts` | rsync | optional; if missing, the host key is fetched |
| `ftp-host`, `ftp-user`, `ftp-pass` | FTP | access |
| `build-env` | build | optional; lines `NAME=value`, set and masked only in the build step, e.g. a token the build needs to fetch content |

Files excluded at the target stay in place with `loeschen: true`; this way
folders such as `.well-known/` can be protected.

About the dry run: a file counts as changed if its content or size differs; a
different timestamp alone does not count. Over FTP the run checks login and
target folder first and aborts if either is missing. A folder deleted there
counts ten times towards the deletion limit, because lftp does not say how many
files it contains.

## Inputs of `secret-scan.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `konfiguration` | `.gitleaks.toml` | gitleaks configuration in the calling repository |

The optional secret `GITLEAKS_EXTRA_RULES` appends further rules that should
not be stored in the repository.

## Inputs of `docker-image.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `image` | – | name without tag, e.g. `ghcr.io/owner/project/server`; without a registry Docker Hub is used |
| `kontext` | `.` | build context |
| `dockerfile` | – | empty: `Dockerfile` in the context |
| `plattformen` | `linux/amd64` | platforms, comma-separated |
| `build-args` | – | lines `NAME=value` |
| `tags` | see below | rules for [docker/metadata-action](https://github.com/docker/metadata-action#tags-input) |
| `hochladen` | `true` | `false`: build only; pull requests never push |
| `node-version` | – | Node for the preparation step |
| `vorbereitung` | – | command before the build, e.g. building a frontend |
| `pruefung` | – | command against the built image (name in `$PRUEFLING`); if it fails, nothing is pushed |
| `registry-benutzer` | – | registry user; empty for ghcr.io: the triggering user |

| Secret | Meaning |
|--------|---------|
| `registry-token` | empty for ghcr.io: the caller's `GITHUB_TOKEN`; for Docker Hub an access token |

Without `tags` the image gets `latest` (on the default branch only),
`sha-<commit>` and, for a version tag, `1.2.3` and `1.2`. The build cache is
kept per image in the GitHub Actions cache. For ghcr.io the job needs
`packages: write`.

## Inputs of `portainer-deploy.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `pruef-url` | – | URL that has to answer afterwards; empty: no check |
| `pruef-status` | `200` | allowed HTTP status codes, separated by spaces |
| `revision-feld` | – | jq path in the JSON response that has to contain the built commit, e.g. `.revision` |
| `wartezeit` | `300` | maximum seconds the check waits |

The secret `webhook` is required. Webhook URLs always belong in a secret:
whoever knows one can redeploy the stack, and variables appear in the log in
plain text.

## Inputs of `xcode-tests.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `projekt` | – | `.xcodeproj` or `.xcworkspace` |
| `schema` | – | scheme |
| `aktion` | `test` | `test` or `build` |
| `test-ziel` | – | only this test target (`-only-testing`) |
| `runner` | `macos-26` | runner image |
| `xcode` | `neuestes` | `neuestes` (newest stable Xcode on the runner), `vorgabe` (do not switch) or path to `Xcode.app` |
| `ohne-signierung` | `false` | build without code signing |
| `vorbereitung` | – | command before the build, e.g. a placeholder for a file not in the repository |
| `artefakt` | – | file provided as an artifact afterwards, e.g. `Package.resolved` |
| `timeout` | `40` | minutes |

Tests run on the newest iPhone simulator of the runner. If the run fails, the
full log is available as the artifact `xcode-log`.

## Inputs of `xcode-cloud.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `workflow-id` | – | ID of the Xcode Cloud workflow (App Store Connect API, `ciWorkflows`) |
| `wartezeit` | `60` | Minutes to wait for the build (at most 100) |

Secrets: `asc-key-id`, `asc-issuer-id` and `asc-key-p8`, the private key of an
App Store Connect API key, base64-encoded. Output: `build-nummer`.

Xcode Cloud always builds the current state of a branch, not a specific commit.
If the branch has already moved on at start, the workflow starts nothing. If
Xcode Cloud built a different commit anyway, the run fails. Upload to
TestFlight and the tester groups are set by the Xcode Cloud workflow itself.

## Inputs of `play-upload.yml`

| Input | Default | Meaning |
|-------|---------|---------|
| `paket` | – | Package name on Google Play |
| `tracks` | – | comma-separated from `internal`, `alpha`, `beta`, `production`; spaces and duplicates are ignored, unknown names abort |
| `artefakt` | – | Artifact with exactly one `.aab` file |
| `status` | `completed` | `completed` releases at once, `draft` creates a draft in the Play Console (the only status while the app has never been published) |
| `production-anteil` | `0.1` | only `production` with `completed`: share of users who get the update first; `1` = everyone |
| `release-notes` | – | Release notes as text |
| `release-notes-datei` | – | Release notes from a file in the repository |
| `sprache` | `de-DE` | Language of the release notes |
| `dry-run` | `false` | upload, set tracks and validate, then discard |
| `nur-pruefen` | `false` | only check inputs and release notes, without network or key |

The secret `dienstkonto` is the JSON key of a Google service account,
base64-encoded; it is not needed with `nur-pruefen`.

Release notes over 500 characters abort before an edit is created; otherwise
Google would only fail at commit, with a message that looks like missing
permissions. 5xx responses and connection errors are retried up to three
times. If a step fails, the edit is discarded. A dry run does not use up a
`versionCode`, but Google rejects an already used one on upload; the caller
builds with a higher number for it.

## Versions

What changed when is in [CHANGELOG.md](CHANGELOG.md) (in German, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)). The
[releases](https://github.com/Revisor01/workflows/releases) summarise each
version.

## Contributing

Bug reports and suggestions are welcome as an
[issue](https://github.com/Revisor01/workflows/issues). Please report security
issues privately as described in [SECURITY.md](SECURITY.md). Pull requests run
through actionlint and a secret scan; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 Simon Luthe

## Contact

Pastor Simon Luthe · [mail@simonluthe.de](mailto:mail@simonluthe.de) ·
[simonluthe.de](https://simonluthe.de)
