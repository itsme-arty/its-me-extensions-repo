# It's Me — personal Mihon extensions (PRIVATE)

Keep this repository **private**. `signing/` holds the key that signs the extensions.
Anyone with it could publish updates that your phone would trust.

## Contents
- `kagane/` – Kagane extension source (based on keiyoushi/extensions-source `src/all/kagane`) with the chapter fix
- `patches/kagane-chapter-fix.diff` – the fix as a patch against upstream
- `tools/make-repo.py` – generates the Mihon repo files (`index.pb`, `index.json`, `apk/`, `icon/`)
- `signing/` – signing key (`signingkey.jks`) and its passwords (`signing.env`)
- `public-repo/` – ready-built files to upload to the **public** repo

## The fix
kagane.org stopped returning `series_books` from `/api/v2/series/{id}`.
Chapters now come from `/api/v2/series/{id}/books/index?fields=List`.
A details-only refresh keeps the existing chapter list.

## Rebuild after a change
1. Clone `https://github.com/keiyoushi/extensions-source`
2. Copy `kagane/` over `src/all/kagane/`
3. Copy `signing/signingkey.jks` to the project root
4. `set -a; . signing/signing.env; set +a`
5. `./gradlew :src:all:kagane:assembleRelease`
6. Bump `versionCode` in `kagane/build.gradle.kts` for every new release
7. Generate the repo files:
   `KAGANE_BUILD=<extensions-source>/src/all/kagane/build python tools/make-repo.py https://raw.githubusercontent.com/<USER>/its-me-extensions-repo/main public-repo 054d463eda004cdb0644d69a9c35e2a7696c1ab524353f8e083ad80c1b7c68ad`
   (needs `pip install "protobuf>=7.35.1"`)
8. Upload the contents of `public-repo/` to the public repo

Signing certificate SHA-256: `054d463eda004cdb0644d69a9c35e2a7696c1ab524353f8e083ad80c1b7c68ad`
