import gzip
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "kei-scripts"))
import index_pb2  # noqa: E402
from google.protobuf import json_format  # noqa: E402

# Usage: make-repo.py <base_url> <out_dir> <signing_cert_sha256> [name] [badge]
base_url, out_dir, signing_key = sys.argv[1].rstrip("/"), Path(sys.argv[2]), sys.argv[3]
repo_name = sys.argv[4] if len(sys.argv) > 4 else "It's Me"
badge = sys.argv[5] if len(sys.argv) > 5 else "ME"
build = Path(os.environ["KAGANE_BUILD"])
info = json.loads((build / "keiyoushi-source-info.json").read_text())
apk = next((build / "outputs/apk/release").glob("*.apk"))
jar = next((build / "outputs/jar/release").glob("*.jar"))
icon = Path(__file__).parent.parent / "kagane/res/mipmap-xhdpi/ic_launcher.png"

if out_dir.exists():
    shutil.rmtree(out_dir)
(out_dir / "apk").mkdir(parents=True)
(out_dir / "icon").mkdir()
shutil.copy(apk, out_dir / "apk" / apk.name)
shutil.copy(jar, out_dir / "apk" / jar.name)
shutil.copy(icon, out_dir / "icon" / f"{info['packageName']}.png")

ext = index_pb2.Extension(
    name=info["name"],
    packageName=info["packageName"],
    resources=index_pb2.Resources(
        apkUrl=f"{base_url}/apk/{apk.name}",
        iconUrl=f"{base_url}/icon/{info['packageName']}.png",
        jarUrl=f"{base_url}/apk/{jar.name}",
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
    name=repo_name,
    badgeLabel=badge,
    signingKey=signing_key,
    contact=index_pb2.Contact(website=base_url),
    extensionList=index_pb2.ExtensionList(extensions=[ext]),
)

(out_dir / "index.json").write_text(
    json_format.MessageToJson(index, always_print_fields_with_no_presence=False, preserving_proto_field_name=True)
)
(out_dir / "index.pb").write_bytes(gzip.compress(index.SerializeToString(deterministic=True), mtime=0))
print("ok", out_dir)
