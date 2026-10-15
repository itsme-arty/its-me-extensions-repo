# It's Me Extensions — project notes

Goal: patched Kagane extension for Mihon (chapter list fix after kagane.org API change), published as a personal Mihon repo.

Repo: itsme-arty/its-me-extensions-repo (to be public). Mihon URL:
https://raw.githubusercontent.com/itsme-arty/its-me-extensions-repo/main/repo/index.pb

Done:
- Kagane 1.6.33: chapters from /api/v2/series/{id}/books/index?fields=List; details-only refresh keeps chapters
- Signing key v2 "It's Me" (sha256 eede21e2...034d), kept only in /root/kagane-signing (never in repo; older keys leaked in git history and are retired)
- Clean repo layout: repo/, src/all/kagane, patches/, scripts/make-repo.py, README, LICENSE

Build env (workspace only): /root/kagane-fix/ext (upstream checkout), /root/build.sh, JDK /root/jdk, SDK /root/android, venv /root/repo-venv.
Build: set -a; . /root/kagane-signing/signing.env; /root/build.sh :src:all:kagane:assembleRelease -x :src:all:kagane:optimizeReleaseResources --no-configuration-cache
Old workspace files archived in /root/workspace-archive.

Backlog: more extensions, repo description/topics (GitHub settings).
