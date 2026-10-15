# Kagane Extension Fix: "No chapters found"

A repaired version of the Kagane source for Mihon and its forks (Komikku and others). Browsing and search already work. The fix makes chapter lists load again after Kagane's latest site update.

## Who it's for
Mihon/Komikku users, starting with the requester, whose Kagane extension shows series normally but says "No chapters found" on every title.

## Core features and experience
- Chapter lists load again for Kagane series.
- Opening a chapter shows its pages. Pages are checked right after the chapter-list fix, because the same site update may also have broken them.
- Browse, search and filters keep working as they do now.
- Library entries already added from Kagane keep working, with no re-migration. If the site changed its series IDs and this turns out to be impossible, the summary will say so clearly.
- The result is a sideloadable APK. The extension version is bumped so Mihon treats it as an update.

## User flow
1. Download the patched APK from the link in the final summary.
2. Install it on the phone. Allow installs from unknown sources if prompted.
3. Open Mihon/Komikku, go to Browse, open Kagane, pick a series, and the chapters appear.
4. Optional: the patch file (.diff) is also provided, so it can be shared or sent upstream as a PR.

## UI/UX feel
No new screens. The extension looks and behaves the same inside the app. The only visible change is that chapters load.

## Implementation phases
- **Phase 1 (MVP, built now):** Clone keiyoushi/extensions-source. Compare the extension's chapter and page requests against what kagane.org's website currently does. Update the endpoints, IDs or response parsing to match. Build the APK, and provide the APK and the diff.
- **Phase 2:** Fix other breakages found along the way, such as cover images, specific filters, or DRM/integrity-token edge cases.
- **Phase 3:** Prepare a clean upstream pull request (description plus changes) for the requester to submit to keiyoushi.

## Assumptions
- The requester gave permission to clone keiyoushi/extensions-source, which is the real source of the extension. The "extensions" repo only holds the built files.
- The fix starts from the latest upstream Kagane code, not from the older copy the requester has installed. The requester said the older copy "works" apart from chapters.
- The APK is built with the project's standard debug/unsigned-style signing. It may not install over the official keiyoushi build because the signatures differ, so the existing extension may need to be uninstalled first. Library entries stay in the app.
- Testing is done by reproducing the extension's requests against kagane.org from the build environment and checking that chapters and pages come back. An Android phone can't be run here, so the final in-app check is up to the requester.
- If kagane.org blocks requests from the build environment (Cloudflare/403), verification will rely on the site's public web requests seen through a browser. The summary will state this limitation.
- If the pending community PR for Kagane's URL change already fixes chapters, it will be reused rather than rewritten.
- No GitHub writes are made on the requester's behalf.
