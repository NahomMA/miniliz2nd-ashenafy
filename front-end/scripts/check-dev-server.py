"""Check what a phone would download from the running Expo server: manifest, Android bundle, and the API proxy.

Usage (from front-end/, with `npx expo start` running):  python3 scripts/check-dev-server.py
"""
import json
import re
import subprocess
import time

LOCAL = "http://127.0.0.1:8081"


def curl(*args: str, timeout: int = 150) -> str:
    return subprocess.run(["curl", "-s", "-m", str(timeout), *args], capture_output=True, text=True).stdout


def main() -> None:
    raw = curl("-H", "expo-platform: android", "-H", "accept: application/expo+json,application/json", LOCAL + "/", timeout=10)
    found = re.search(r"\{.*\}", raw, re.S)
    if not found:
        raise SystemExit(f"No manifest from the Expo server at {LOCAL}. Is `npx expo start` running?\n{raw[:200]}")
    manifest = json.loads(found.group(0))
    client = manifest["extra"]["expoClient"]
    bundle_url = manifest["launchAsset"]["url"]
    public_host = re.match(r"https?://[^/]+", bundle_url).group(0)
    print(f"app: {client.get('name')} | sdk: {client.get('sdkVersion')} | served at: {public_host}")

    for label, url in (("bundle, local", LOCAL + bundle_url[len(public_host):]), ("bundle, as the phone sees it", bundle_url)):
        started = time.time()
        body = curl("-w", "\n%{http_code}", url)
        status = body.rsplit("\n", 1)[-1]
        print(f"{label}: HTTP {status}, {len(body):,} bytes, {time.time() - started:.0f}s")
        if status != "200":
            print("   ", body[:700].replace("\n", " "))

    print("api through Expo, local:", curl(LOCAL + "/api/health", timeout=15)[:200])
    print("api through Expo, as the phone sees it:", curl(public_host + "/api/health", timeout=20)[:200])


if __name__ == "__main__":
    main()
