# Backend tests for Kagane private extensions repo (keiyoushi-format)
import gzip
import hashlib
import json
import os
import subprocess
import sys

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://kagane-patch.preview.emergentagent.com").rstrip("/")
REPO_URL = f"{BASE_URL}/repo"
REPO_DIR = "/app/frontend/public/repo"
KEI_SCRIPTS = "/app/kagane-fix/kei-scripts"
APK_PATH = f"{REPO_DIR}/apk/tachiyomi-all.kagane-v1.6.33.apk"
JAR_PATH = f"{REPO_DIR}/apk/tachiyomi-all.kagane-v1.6.33.jar"
ICON_PATH = f"{REPO_DIR}/icon/eu.kanade.tachiyomi.extension.all.kagane.png"
EXPECTED_SIGNING_KEY = "e2b9220aba679d713db81ac3356abef5c3f5f480d837e387b2d578977bfe66b6"
EXPECTED_PACKAGE = "eu.kanade.tachiyomi.extension.all.kagane"


def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _fetch_pb():
    r = requests.get(f"{REPO_URL}/index.pb", timeout=30)
    assert r.status_code == 200, f"index.pb HTTP {r.status_code}"
    raw = gzip.decompress(r.content)
    sys.path.insert(0, KEI_SCRIPTS)
    import index_pb2
    idx = index_pb2.Index()
    idx.ParseFromString(raw)
    return idx, r


# ---------------- index.pb ----------------

class TestIndexPb:
    def test_http_200_and_gzip_parseable(self):
        idx, _ = _fetch_pb()
        assert idx.name == "Jo Private"
        assert idx.badgeLabel == "JO"
        sk = idx.signingKey
        sk_hex = sk.hex() if isinstance(sk, (bytes, bytearray)) else str(sk)
        assert sk_hex.lower() == EXPECTED_SIGNING_KEY

    def test_single_extension_metadata(self):
        idx, _ = _fetch_pb()
        exts = idx.extensionList.extensions
        assert len(exts) == 1, f"expected 1 extension, got {len(exts)}"
        e = exts[0]
        assert e.packageName == EXPECTED_PACKAGE
        assert e.versionName == "1.6.33"
        assert e.versionCode == 106033
        assert e.extensionLib == "1.6"
        # ContentWarning MIXED enum = 3 (per keiyoushi proto)
        import index_pb2
        assert e.contentWarning == index_pb2.CONTENT_WARNING_MIXED

    def test_18_sources_match_keiyoushi(self):
        idx, _ = _fetch_pb()
        e = idx.extensionList.extensions[0]
        assert len(e.sources) == 18
        # Fetch upstream keiyoushi for same package
        try:
            upstream = requests.get(
                "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.json",
                timeout=20,
            ).json()
        except Exception as ex:
            pytest.skip(f"Upstream keiyoushi unreachable: {ex}")
        up_ext = [x for x in upstream["extensionList"]["extensions"]
                  if x["packageName"] == EXPECTED_PACKAGE][0]
        up_ids = sorted(int(s["id"]) for s in up_ext["sources"])
        our_ids = sorted(int(s.id) for s in e.sources)
        assert up_ids == our_ids, "Source IDs don't match keiyoushi; existing library entries will break"


# ---------------- index.json ----------------

class TestIndexJson:
    def test_http_200(self):
        r = requests.get(f"{REPO_URL}/index.json", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Jo Private"
        assert data["badgeLabel"] == "JO"
        assert data["signingKey"] == EXPECTED_SIGNING_KEY

    def test_consistent_with_pb(self):
        idx, _ = _fetch_pb()
        with open(f"{REPO_DIR}/index.json") as f:
            j = json.load(f)
        pb_ext = idx.extensionList.extensions[0]
        j_ext = j["extensionList"]["extensions"][0]
        assert j_ext["packageName"] == pb_ext.packageName
        assert j_ext["versionName"] == pb_ext.versionName
        assert int(j_ext["versionCode"]) == pb_ext.versionCode
        assert len(j_ext["sources"]) == len(pb_ext.sources)
        j_ids = sorted(int(s["id"]) for s in j_ext["sources"])
        pb_ids = sorted(int(s.id) for s in pb_ext.sources)
        assert j_ids == pb_ids

    def test_no_emergent_branding_other_than_host(self):
        with open(f"{REPO_DIR}/index.json") as f:
            text = f.read()
        # Allow emergentagent.com in URLs; forbid 'emergent' elsewhere
        lowered = text.lower()
        # Strip URL occurrences
        import re
        stripped = re.sub(r"https?://[^\s\"]*emergentagent\.com[^\s\"]*", "", lowered)
        assert "emergent" not in stripped, "Found 'emergent' branding outside hosting URL"


# ---------------- Resources (apk/jar/icon) ----------------

class TestResources:
    def test_apk_url_200_and_sha(self):
        r = requests.get(f"{REPO_URL}/apk/tachiyomi-all.kagane-v1.6.33.apk", timeout=60)
        assert r.status_code == 200
        assert hashlib.sha256(r.content).hexdigest() == _sha256(APK_PATH)

    def test_jar_url_200_and_sha(self):
        r = requests.get(f"{REPO_URL}/apk/tachiyomi-all.kagane-v1.6.33.jar", timeout=60)
        assert r.status_code == 200
        assert hashlib.sha256(r.content).hexdigest() == _sha256(JAR_PATH)

    def test_icon_url_200_and_sha(self):
        r = requests.get(f"{REPO_URL}/icon/eu.kanade.tachiyomi.extension.all.kagane.png", timeout=30)
        assert r.status_code == 200
        assert hashlib.sha256(r.content).hexdigest() == _sha256(ICON_PATH)

    def test_jar_signed_by_jo_private(self):
        # Use jarsigner since .jar may use v1 scheme; apksigner also works
        java = "/root/jdk/jdk-21"
        import glob
        jdk_dirs = glob.glob("/root/jdk/jdk-21*")
        assert jdk_dirs, "JDK 21 not found"
        jarsigner = f"{jdk_dirs[0]}/bin/jarsigner"
        if not os.path.exists(jarsigner):
            # fallback to apksigner on jar
            apksigner = "/root/android/build-tools/37.0.0/lib/apksigner.jar"
            out = subprocess.run(
                [f"{jdk_dirs[0]}/bin/java", "-jar", apksigner, "verify", "--print-certs", JAR_PATH],
                capture_output=True, text=True
            )
            assert "Jo Private" in out.stdout, out.stdout + out.stderr
        else:
            out = subprocess.run([jarsigner, "-verify", "-verbose", "-certs", JAR_PATH],
                                 capture_output=True, text=True)
            assert "jar verified" in out.stdout.lower(), out.stdout + out.stderr
            assert "Jo Private" in out.stdout

    def test_apk_signing_cert_matches_signingkey(self):
        import glob
        jdk_dirs = glob.glob("/root/jdk/jdk-21*")
        assert jdk_dirs
        java = f"{jdk_dirs[0]}/bin/java"
        apksigner = "/root/android/build-tools/37.0.0/lib/apksigner.jar"
        out = subprocess.run(
            [java, "-jar", apksigner, "verify", "--print-certs", APK_PATH],
            capture_output=True, text=True
        )
        combined = out.stdout + out.stderr
        assert EXPECTED_SIGNING_KEY in combined.lower(), \
            f"APK cert SHA-256 does not match index signingKey.\n{combined}"
