# Kagane extension fix (Mihon/Komikku)
Problem: Kagane (keiyoushi, v1.6.32) shows series but "No chapters found" after kagane.org update.
Root cause: /api/v2/series/{id} no longer returns series_books; chapters now come from /api/v2/series/{id}/books/index?fields=List (compact fields+rows format).
Done (2026-10-15):
- Applied upstream PR #19986 + maintainer review fixes (details-only refresh keeps existing chapters; details fetched only when needed; format cached in memo; tolerant index parsing)
- Built v1.6.33 APK/JAR (ARM64 host; aapt2 optimize step run manually). Served at /kagane/ on preview URL. Source at /app/kagane-fix/ext, diff at /app/kagane-fix/kagane-chapter-fix.diff
Not verified: live API (Cloudflare blocks build env); in-app test is up to user.
Backlog: personal extension repo (user paused it), upstream PR.
