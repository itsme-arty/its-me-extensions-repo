"""Generate the Mihon repo index (index.pb / index.json) for the built Kagane extension.

Usage: make-repo.py <kagane_build_dir> <signing_cert_sha256>
"""

import gzip
import json
import shutil
import sys
from pathlib import Path

from google.protobuf import json_format

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import index_pb2  # noqa: E402

BASE_URL = "https://raw.githubusercontent.com/itsme-arty/its-me-extensions-repo/main/repo"
REPO_DIR = ROOT / "repo"

build, signing_key = Path(sys.argv[1]), sys.argv[2]
info = json.loads((build / "keiyoushi-source-info.json").read_text())
apk = next((build / "outputs/apk/release").glob("*.apk"))
jar = next((build / "outputs/jar/release").glob("*.jar"))
pkg = info["packageName"]

shutil.rmtree(REPO_DIR, ignore_errors=True)
(REPO_DIR / "apk").mkdir(parents=True)
(REPO_DIR / "icon").mkdir()
shutil.copy(apk, REPO_DIR / "apk" / apk.name)
shutil.copy(jar, REPO_DIR / "apk" / jar.name)
shutil.copy(ROOT / "src/all/kagane/res/mipmap-xhdpi/ic_launcher.png", REPO_DIR / "icon" / f"{pkg}.png")

ext = index_pb2.Extension(
    name=info["name"],
    packageName=pkg,
    resources=index_pb2.Resources(
        apkUrl=f"{BASE_URL}/apk/{apk.name}",
        iconUrl=f"{BASE_URL}/icon/{pkg}.png",
        jarUrl=f"{BASE_URL}/apk/{jar.name}",
    ),
    extensionLib=info["extensionLib"],
    versionCode=info["versionCode"],
    versionName=info["versionName"],
    contentWarning=info["contentWarning"],
    sources=[
        index_pb2.Source(
            id=int(s["id"]),
            name=s["name"],
            language=s["lang"],
            homeUrl=s["baseUrl"],
            mirrorUrls=s.get("mirrorUrls", []),
        )
        for s in info["sources"]
    ],
)

index = index_pb2.Index(
    name="It's Me",
    badgeLabel="ME",
    signingKey=signing_key,
    contact=index_pb2.Contact(website="https://github.com/itsme-arty/its-me-extensions-repo"),
    extensionList=index_pb2.ExtensionList(extensions=[ext]),
)

(REPO_DIR / "index.json").write_text(
    json_format.MessageToJson(index, always_print_fields_with_no_presence=False, preserving_proto_field_name=True) + "\n"
)
(REPO_DIR / "index.pb").write_bytes(gzip.compress(index.SerializeToString(deterministic=True), mtime=0))
print("updated", REPO_DIR)
