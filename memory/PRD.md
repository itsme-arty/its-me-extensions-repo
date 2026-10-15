# Kagane extension fix (Mihon/Komikku)
Problem: Kagane (keiyoushi, v1.6.32) shows series but "No chapters found" after kagane.org update.
Root cause: /api/v2/series/{id} no longer returns series_books; chapters now come from /api/v2/series/{id}/books/index?fields=List (compact fields+rows format).
Done (2026-10-15):
- Applied upstream PR #19986 + maintainer review fixes (details-only refresh keeps existing chapters; details fetched only when needed; format cached in memo; tolerant index parsing)
- Built v1.6.33 APK/JAR (ARM64 host; aapt2 optimize step run manually). Served at /kagane/ on preview URL. Source at /app/kagane-fix/ext, diff at /app/kagane-fix/kagane-chapter-fix.diff
Not verified: live API (Cloudflare blocks build env); in-app test is up to user.
Backlog: personal extension repo (user paused it), upstream PR.
- 2026-10-15: Play Protect "harmful" warning fixed: re-signed with personal release key (CN=Jo Private Extensions), keystore + passwords in /root/kagane-signing (keep for future updates). Build: set -a; . /root/kagane-signing/signing.env; /root/build.sh :src:all:kagane:assembleRelease -x :src:all:kagane:optimizeReleaseResources --no-configuration-cache (run aapt2 optimize manually first if resources change).
- 2026-10-15: Private Mihon repo "Jo Private" (keiyoushi index.pb format) at <preview>/repo/index.pb, files in /app/frontend/public/repo, generator: /root/repo-venv/bin/python /app/kagane-fix/make-repo.py <base_url> <out_dir> <cert_sha256>. Next: move to user's GitHub for permanent hosting.
- 2026-10-15: Rebranded to "It's Me" (badge ME), new key CN=It's Me (sha256 054d463e...); old Jo key in /root/kagane-signing/old-jo. Private-repo folder /app/its-me-extensions (source, patch, tools, signing, public-repo with YOUR_GITHUB_USERNAME placeholder). Live preview repo at <preview>/repo/index.pb. Pending: user's GitHub username -> regenerate public-repo with real raw URL.
