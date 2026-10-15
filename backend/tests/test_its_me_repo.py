"""
Backend tests for 'It's Me' Kagane repo rebrand.
Tests the live hosted repo files, APK/JAR signatures, folder structure, and make-repo.py tool.
"""
import os
import sys
import gzip
import json
import re
import subprocess
import hashlib
import io
import zipfile
import pytest
import requests

LIVE_BASE = "https://kagane-patch.preview.emergentagent.com"
EXPECTED_SIGNING_KEY = "054d463eda004cdb0644d69a9c35e2a7696c1ab524353f8e083ad80c1b7c68ad"
EXPECTED_NAME = "It's Me"
EXPECTED_BADGE = "ME"
EXPECTED_VERSION = "1.6.33"
EXPECTED_SOURCES = 18

APKSIGNER_JAR = "/root/android/build-tools/37.0.0/lib/apksigner.jar"
JAVA_BIN = None  # discovered

sys.path.insert(0, "/app/kagane-fix/kei-scripts")
sys.path.insert(0, "/app/its-me-extensions/tools/kei-scripts")


def _find_java():
    global JAVA_BIN
    if JAVA_BIN:
        return JAVA_BIN
    import glob
    cands = glob.glob("/root/jdk/jdk-21*/bin/java")
    if cands:
        JAVA_BIN = cands[0]
        return JAVA_BIN
    return None


# ========== Live repo tests ==========

class TestLiveRepo:
    def test_index_pb_reachable(self):
        r = requests.get(f"{LIVE_BASE}/repo/index.pb", timeout=15)
        assert r.status_code == 200, r.status_code
        self._raw = r.content
        assert len(r.content) > 10

    def test_index_pb_parse(self):
        r = requests.get(f"{LIVE_BASE}/repo/index.pb", timeout=15)
        assert r.status_code == 200
        raw = r.content
        # try gunzip
        try:
            data = gzip.decompress(raw)
        except OSError:
            data = raw
        # Import protobuf
        try:
            import index_pb2
        except Exception as e:
            pytest.fail(f"Cannot import index_pb2: {e}")

        idx = index_pb2.Index()
        idx.ParseFromString(data)

        assert idx.name == EXPECTED_NAME, f"name={idx.name!r}"
        assert idx.badgeLabel == EXPECTED_BADGE, f"badgeLabel={idx.badgeLabel!r}"
        assert idx.signingKey == EXPECTED_SIGNING_KEY, f"signingKey={idx.signingKey!r}"
        assert len(idx.extensionList.extensions) == 1
        ext = idx.extensionList.extensions[0]
        assert "kagane" in ext.packageName.lower() or ext.name.lower().startswith("kagane"), ext.packageName
        assert ext.versionName == EXPECTED_VERSION, f"versionName={ext.versionName}"
        assert len(ext.sources) == EXPECTED_SOURCES, f"sources={len(ext.sources)}"

        # Save for next test
        TestLiveRepo.apk_url = ext.resources.apkUrl
        TestLiveRepo.jar_url = ext.resources.jarUrl if hasattr(ext, "jarUrl") else None
        TestLiveRepo.icon_url = ext.resources.iconUrl
        print(f"apkUrl={ext.resources.apkUrl}")
        print(f"iconUrl={ext.resources.iconUrl}")

    def test_artifact_urls_200(self):
        r = requests.get(f"{LIVE_BASE}/repo/index.pb", timeout=15)
        raw = r.content
        try:
            data = gzip.decompress(raw)
        except OSError:
            data = raw
        import index_pb2
        idx = index_pb2.Index()
        idx.ParseFromString(data)
        ext = idx.extensionList.extensions[0]

        for url in [ext.resources.apkUrl, ext.resources.iconUrl]:
            if not url:
                continue
            hr = requests.head(url, timeout=15, allow_redirects=True)
            if hr.status_code != 200:
                hr = requests.get(url, timeout=20, stream=True)
            assert hr.status_code == 200, f"{url} -> {hr.status_code}"

        # jarUrl - sibling to apk
        jar_url = ext.resources.apkUrl.replace(".apk", ".jar")
        hr = requests.get(jar_url, timeout=20, stream=True)
        assert hr.status_code == 200, f"{jar_url} -> {hr.status_code}"


# ========== APK/JAR signature verification ==========

class TestSignatures:
    @classmethod
    def setup_class(cls):
        r = requests.get(f"{LIVE_BASE}/repo/index.pb", timeout=15)
        raw = r.content
        try:
            data = gzip.decompress(raw)
        except OSError:
            data = raw
        import index_pb2
        idx = index_pb2.Index()
        idx.ParseFromString(data)
        ext = idx.extensionList.extensions[0]
        cls.apk_url = ext.resources.apkUrl
        cls.jar_url = ext.resources.apkUrl.replace(".apk", ".jar")

        # Download
        cls.apk_path = "/tmp/test_itsme.apk"
        cls.jar_path = "/tmp/test_itsme.jar"
        with open(cls.apk_path, "wb") as f:
            f.write(requests.get(cls.apk_url, timeout=60).content)
        with open(cls.jar_path, "wb") as f:
            f.write(requests.get(cls.jar_url, timeout=60).content)

    def test_apksigner_verify(self):
        java = _find_java()
        assert java, "java not found"
        assert os.path.exists(APKSIGNER_JAR), APKSIGNER_JAR
        out = subprocess.run(
            [java, "-jar", APKSIGNER_JAR, "verify", "--print-certs", self.apk_path],
            capture_output=True, text=True, timeout=60
        )
        print("STDOUT:", out.stdout)
        print("STDERR:", out.stderr)
        combined = out.stdout + out.stderr
        assert out.returncode == 0, f"apksigner verify failed: {combined}"
        # Cert DN check
        assert "CN=It's Me" in combined, f"CN not found: {combined[:500]}"
        assert "O=It's Me" in combined, f"O not found: {combined[:500]}"
        # SHA-256 digest
        m = re.search(r"SHA-256 digest:\s*([0-9a-fA-F]{64})", combined)
        assert m, f"SHA-256 digest not found in: {combined[:800]}"
        sha = m.group(1).lower()
        assert sha == EXPECTED_SIGNING_KEY, f"cert sha256 {sha} != {EXPECTED_SIGNING_KEY}"

    def test_apk_contents(self):
        with zipfile.ZipFile(self.apk_path) as z:
            names = z.namelist()
            assert "AndroidManifest.xml" in names
            assert "resources.arsc" in names
            dex = [n for n in names if n.endswith(".dex")]
            assert dex, "no classes.dex"
            # Check 'books/index' string present in any dex
            found = False
            for d in dex:
                if b"books/index" in z.read(d):
                    found = True
                    break
            assert found, "'books/index' not found in dex"

    def test_jarsigner_verify(self):
        import glob
        jarsigner_cands = glob.glob("/root/jdk/jdk-21*/bin/jarsigner")
        if not jarsigner_cands:
            pytest.skip("jarsigner not found")
        jarsigner = jarsigner_cands[0]
        out = subprocess.run(
            [jarsigner, "-verify", "-verbose", "-certs", self.jar_path],
            capture_output=True, text=True, timeout=60
        )
        combined = out.stdout + out.stderr
        print("JAR verify:", combined[:1500])
        assert "jar verified" in combined.lower(), f"jar not verified: {combined[:500]}"
        assert "CN=It's Me" in combined, f"CN not in jar signer: {combined[:500]}"


# ========== Old branding removed ==========

class TestOldBrandingRemoved:
    def test_old_apk_url_not_serving(self):
        url = f"{LIVE_BASE}/kagane/tachiyomi-all.kagane-v1.6.33.apk"
        r = requests.get(url, timeout=15, allow_redirects=True)
        # Must NOT be an APK: either 404 or HTML fallback
        ctype = r.headers.get("content-type", "")
        is_apk = r.content[:4] == b"PK\x03\x04" and r.status_code == 200 and len(r.content) > 100000 and "apk" in ctype.lower()
        # It's okay if it serves HTML (SPA fallback)
        assert not is_apk, f"Old APK still served: status={r.status_code}, ctype={ctype}, len={len(r.content)}"

    def test_no_jo_private_or_emergent_in_files(self):
        """Scan /app/frontend/public/repo and /app/its-me-extensions for forbidden strings.
        Exception: hosting URL 'emergent' allowed under /app/frontend/public/repo index files."""
        forbidden = [b"Jo Private", b"jo private", b"JO PRIVATE"]
        emergent_pat = re.compile(rb"emergent", re.IGNORECASE)

        bad = []
        for root in ["/app/its-me-extensions", "/app/frontend/public/repo"]:
            for dirpath, _, files in os.walk(root):
                for fn in files:
                    p = os.path.join(dirpath, fn)
                    try:
                        with open(p, "rb") as f:
                            content = f.read()
                    except Exception:
                        continue
                    for fw in forbidden:
                        if fw in content:
                            bad.append((p, fw.decode("latin-1", "replace")))
                    if emergent_pat.search(content):
                        # Allowed only in frontend/public/repo index files (hosting URL)
                        if root == "/app/frontend/public/repo" and fn in ("index.pb", "index.json", "index.min.json"):
                            continue
                        # Also allow in icon paths? Only index files allowed.
                        bad.append((p, "emergent"))
        assert not bad, f"Forbidden strings found: {bad[:20]}"


# ========== Folder structure ==========

class TestFolderStructure:
    def test_required_files_exist(self):
        base = "/app/its-me-extensions"
        required = [
            "README.md",
            "kagane/build.gradle.kts",
            "kagane/src/eu/kanade/tachiyomi/extension/all/kagane/Kagane.kt",
            "kagane/src/eu/kanade/tachiyomi/extension/all/kagane/Dto.kt",
            "patches/kagane-chapter-fix.diff",
            "tools/make-repo.py",
            "tools/kei-scripts/index.proto",
            "tools/kei-scripts/index_pb2.py",
            "signing/signingkey.jks",
            "signing/signing.env",
            "public-repo/index.pb",
            "public-repo/index.json",
            "public-repo/README.md",
        ]
        for rel in required:
            p = os.path.join(base, rel)
            assert os.path.exists(p), f"missing: {p}"

        # res dir
        assert os.path.isdir(os.path.join(base, "kagane/res"))
        # apk + jar + icon
        apks = os.listdir(os.path.join(base, "public-repo/apk"))
        assert any(a.endswith(".apk") for a in apks), apks
        assert any(a.endswith(".jar") for a in apks), apks
        icons = os.listdir(os.path.join(base, "public-repo/icon"))
        assert any(i.endswith(".png") for i in icons), icons

    def test_build_gradle_version(self):
        with open("/app/its-me-extensions/kagane/build.gradle.kts") as f:
            c = f.read()
        assert "versionCode = 33" in c, c

    def test_public_repo_no_signing(self):
        for dirpath, _, files in os.walk("/app/its-me-extensions/public-repo"):
            for fn in files:
                lower = fn.lower()
                assert "signing" not in lower, f"signing file in public-repo: {os.path.join(dirpath, fn)}"
                assert not lower.endswith(".jks"), f"keystore in public-repo: {fn}"
                assert not lower.endswith(".env"), f".env in public-repo: {fn}"

    def test_public_repo_index_uses_placeholder(self):
        # Parse public-repo/index.pb
        with open("/app/its-me-extensions/public-repo/index.pb", "rb") as f:
            raw = f.read()
        try:
            data = gzip.decompress(raw)
        except OSError:
            data = raw
        import index_pb2
        idx = index_pb2.Index()
        idx.ParseFromString(data)
        assert idx.name == EXPECTED_NAME
        assert idx.signingKey == EXPECTED_SIGNING_KEY
        ext = idx.extensionList.extensions[0]
        expected_base = "https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/its-me-extensions-repo/main"
        assert ext.resources.apkUrl.startswith(expected_base), f"apkUrl={ext.resources.apkUrl}"
        assert ext.resources.iconUrl.startswith(expected_base), f"iconUrl={ext.resources.iconUrl}"

        # index.json also check
        with open("/app/its-me-extensions/public-repo/index.json") as f:
            j = json.load(f)
        s = json.dumps(j)
        assert "YOUR_GITHUB_USERNAME" in s or expected_base in s, "placeholder base not found in index.json"
        assert EXPECTED_SIGNING_KEY in s


# ========== make-repo.py tool ==========

class TestMakeRepoTool:
    def test_make_repo_runs(self):
        env = os.environ.copy()
        env["KAGANE_BUILD"] = "/app/kagane-fix/ext/src/all/kagane/build"
        out_dir = "/tmp/testrepo_itsme"
        subprocess.run(["rm", "-rf", out_dir], check=False)

        py = "/root/repo-venv/bin/python"
        if not os.path.exists(py):
            pytest.skip(f"{py} missing")

        if not os.path.isdir(env["KAGANE_BUILD"]):
            pytest.skip(f"KAGANE_BUILD missing: {env['KAGANE_BUILD']}")

        res = subprocess.run(
            [py, "/app/its-me-extensions/tools/make-repo.py",
             "https://example.com/x", out_dir, EXPECTED_SIGNING_KEY],
            env=env, capture_output=True, text=True, timeout=120
        )
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        assert res.returncode == 0, f"make-repo failed: {res.stderr}"

        idx_path = os.path.join(out_dir, "index.pb")
        assert os.path.exists(idx_path), f"missing {idx_path}"
        with open(idx_path, "rb") as f:
            raw = f.read()
        try:
            data = gzip.decompress(raw)
        except OSError:
            data = raw
        import index_pb2
        idx = index_pb2.Index()
        idx.ParseFromString(data)
        assert idx.name == EXPECTED_NAME
        assert idx.signingKey == EXPECTED_SIGNING_KEY
        ext = idx.extensionList.extensions[0]
        assert ext.resources.apkUrl.startswith("https://example.com/x"), ext.resources.apkUrl
        assert ext.resources.iconUrl.startswith("https://example.com/x"), ext.resources.iconUrl
