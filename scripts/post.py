"""Posting otomatis ke Instagram lewat Instagram API (Instagram Login).

Mengambil folder paling awal di queue/ yang tanggalnya sudah tiba (WIB),
memposting gambar di dalamnya (1 gambar = post biasa, 2-10 = carousel),
lalu memindahkan folder itu ke posted/.

Env wajib : IG_USER_ID, IG_ACCESS_TOKEN, GITHUB_REPOSITORY
Env opsional: GITHUB_REF_NAME (default main), API_VERSION (default v21.0),
              DRY_RUN=1 (hanya cek, tidak memposting)
"""
import json
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "queue")
POSTED = os.path.join(ROOT, "posted")
WIB = timezone(timedelta(hours=7))
IMAGE_EXT = (".jpg", ".jpeg")


def api(method, path, params):
    base = f"https://graph.instagram.com/{os.environ.get('API_VERSION', 'v21.0')}"
    params = dict(params, access_token=os.environ["IG_ACCESS_TOKEN"])
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{base}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{base}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        # jangan tampilkan token di log
        sys.exit(f"API error {e.code} pada {path}: {body}")


def wait_ready(container_id):
    for _ in range(30):
        status = api("GET", container_id, {"fields": "status_code"}).get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {container_id} gagal: {status}")
        time.sleep(5)
    sys.exit(f"Container {container_id} belum siap setelah 150 detik")


def next_folder():
    today = datetime.now(WIB).strftime("%Y-%m-%d")
    folders = sorted(
        d for d in os.listdir(QUEUE)
        if os.path.isdir(os.path.join(QUEUE, d)) and d[:10] <= today
    )
    return folders[0] if folders else None


def main():
    folder = next_folder()
    if not folder:
        print("Antrean kosong / belum ada yang jadwalnya hari ini. Selesai.")
        return

    path = os.path.join(QUEUE, folder)
    images = sorted(f for f in os.listdir(path) if f.lower().endswith(IMAGE_EXT))
    caption_file = os.path.join(path, "caption.txt")
    caption = open(caption_file, encoding="utf-8").read().strip() if os.path.exists(caption_file) else ""

    if not images:
        sys.exit(f"{folder}: tidak ada gambar .jpg (Instagram API hanya menerima JPEG)")
    if len(images) > 10:
        sys.exit(f"{folder}: maksimal 10 gambar per carousel, ada {len(images)}")

    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    urls = [
        f"https://raw.githubusercontent.com/{repo}/{branch}/queue/"
        f"{urllib.parse.quote(folder)}/{urllib.parse.quote(img)}"
        for img in images
    ]

    print(f"Folder : {folder}")
    print(f"Gambar : {len(images)} ({'carousel' if len(images) > 1 else 'post biasa'})")
    print(f"Caption: {caption[:80]}{'...' if len(caption) > 80 else ''}")

    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN aktif: tidak memposting.")
        return

    user = os.environ["IG_USER_ID"]
    if len(urls) == 1:
        container = api("POST", f"{user}/media", {"image_url": urls[0], "caption": caption})["id"]
    else:
        children = []
        for url in urls:
            cid = api("POST", f"{user}/media", {"image_url": url, "is_carousel_item": "true"})["id"]
            wait_ready(cid)
            children.append(cid)
        container = api("POST", f"{user}/media", {
            "media_type": "CAROUSEL", "children": ",".join(children), "caption": caption,
        })["id"]

    wait_ready(container)
    media = api("POST", f"{user}/media_publish", {"creation_id": container})
    print(f"Terposting! media id: {media.get('id')}")

    os.makedirs(POSTED, exist_ok=True)
    shutil.move(path, os.path.join(POSTED, folder))


if __name__ == "__main__":
    main()
