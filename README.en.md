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
