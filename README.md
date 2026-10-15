# It's Me Extensions

Personal extension repository for [Mihon](https://mihon.app) and its forks (Komikku, etc.).

It currently ships a patched **Kagane** extension that loads chapter lists again after
kagane.org changed its API.

## Add the repo

In Mihon: **More → Settings → Browse → Extension repos → Add**, then paste:

```
https://raw.githubusercontent.com/itsme-arty/its-me-extensions-repo/main/repo/index.pb
```

Then open **Browse → Extensions** and install Kagane (badge `ME`).

> If Kagane from another repo is already installed, uninstall it first. Extensions signed
> with a different key can't be updated in place. Your library is not affected.

## Extensions

| Extension | Version | Languages | Notes |
|-----------|---------|-----------|-------|
| Kagane    | 1.6.33  | 18        | Chapter list fix |

## What changed in Kagane

kagane.org no longer returns `series_books` from `/api/v2/series/{id}`, so the extension
reported "No chapters found" on every title. Chapters now come from:

```
GET /api/v2/series/{id}/books/index?fields=List
```

The response is a compact table (`fields` + `books` rows), which is now parsed into chapters.
A details-only refresh also keeps the existing chapter list instead of clearing it.

The full change is in [`patches/kagane-chapter-fix.diff`](patches/kagane-chapter-fix.diff).

## Layout

```
repo/       Built files Mihon downloads (index.pb, index.json, apk/, icon/)
src/        Extension source
patches/    The fix as a patch against upstream
scripts/    Repo index generator
```

## Building

The source is meant to be dropped into a checkout of
[keiyoushi/extensions-source](https://github.com/keiyoushi/extensions-source):

1. Copy `src/all/kagane` over the same path in the upstream checkout.
2. Put your `signingkey.jks` in the project root and export `KEY_STORE_PASSWORD`, `ALIAS`
   and `KEY_PASSWORD`.
3. Build: `./gradlew :src:all:kagane:assembleRelease`
4. Regenerate the index (needs `pip install "protobuf>=7.35.1"`):
   `python scripts/make-repo.py <checkout>/src/all/kagane/build <certificate-sha256>`

Bump `versionCode` in `src/all/kagane/build.gradle.kts` for every release so Mihon offers the update.

Signing certificate SHA-256:
`eede21e2514d4f2251d9541e7504915a8963148d9c4090f54301d31c4f21034d`

## Credits

Based on the Kagane extension from [keiyoushi/extensions-source](https://github.com/keiyoushi/extensions-source),
including the fix proposed in [#19986](https://github.com/keiyoushi/extensions-source/pull/19986).

## License

[Apache License 2.0](LICENSE), same as upstream.
