#!/usr/bin/env python3
import json
import shutil
import threading
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


N = 4

BASE_URL = "https://ftp.ebi.ac.uk/empiar/world_availability/12870/data/RAW_Tif/"
INPUT = Path("tif.json")
TMP_DIR = Path("tmp")
TIFS_DIR = Path("tifs")
RESULT_DIR = Path("result")
WAIT_SECONDS = 10
MAX_TIFS = 40
CHUNK_SIZE = 1024 * 1024
CAPACITY_LOCK = threading.Lock()


def load_filenames():
    with INPUT.open() as file:
        filenames = json.load(file)

    if not isinstance(filenames, list) or not all(isinstance(name, str) for name in filenames):
        raise ValueError(f"{INPUT} must contain a JSON array of filenames")

    return filenames


def has_result(stem):
    if not RESULT_DIR.exists():
        return False

    return any(path.is_file() and path.stem.startswith(stem) for path in RESULT_DIR.iterdir())


def file_url(filename):
    return BASE_URL + quote(filename)


def wait_for_capacity():
    while True:
        tif_count = sum(
            1
            for path in TIFS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in (".tif", ".tiff")
        )
        if tif_count <= MAX_TIFS:
            return

        print(f"{TIFS_DIR} has {tif_count} tif files; sleeping {WAIT_SECONDS}s")
        time.sleep(WAIT_SECONDS)


def download_to_tmp(filename, thread_id):
    tmp_path = TMP_DIR / f"thread-{thread_id}-{filename}"
    part_path = tmp_path.with_name(tmp_path.name + ".part")

    while True:
        try:
            request = Request(
                file_url(filename),
                headers={"User-Agent": "mk6420-tif-downloader/1.0"},
            )
            with urlopen(request, timeout=60) as response, part_path.open("wb") as output:
                shutil.copyfileobj(response, output, length=CHUNK_SIZE)

            part_path.replace(tmp_path)
            return tmp_path
        except Exception as exc:
            part_path.unlink(missing_ok=True)
            print(f"thread {thread_id}: failed to download {filename}: {exc}; retrying")
            time.sleep(WAIT_SECONDS)


def worker(thread_id, filenames):
    for filename in filenames:
        tif_path = Path(filename)
        stem = tif_path.stem

        if has_result(stem):
            print(f"thread {thread_id}: skipping completed {stem}")
            continue

        wait_for_capacity()
        tmp_path = download_to_tmp(filename, thread_id)
        target_path = TIFS_DIR / tif_path.name
        with CAPACITY_LOCK:
            wait_for_capacity()
            shutil.copy2(tmp_path, target_path)
            tmp_path.unlink(missing_ok=True)
        print(f"thread {thread_id}: copied {target_path}")


def main():
    if N <= 0:
        raise ValueError("N must be greater than 0")

    TMP_DIR.mkdir(exist_ok=True)
    TIFS_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)

    filenames = load_filenames()
    threads = []
    for thread_id in range(N):
        thread_filenames = [
            filename for index, filename in enumerate(filenames) if index % N == thread_id
        ]
        thread = threading.Thread(
            target=worker,
            args=(thread_id, thread_filenames),
            name=f"download-{thread_id}",
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
