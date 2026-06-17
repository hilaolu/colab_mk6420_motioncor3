#!/usr/bin/env python3
import json
import shutil
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://ftp.ebi.ac.uk/empiar/world_availability/12870/data/RAW_Tif/"
INPUT = Path("tif.json")
OUTPUT_DIR = Path("tif")
CHUNK_SIZE = 1024 * 1024
RETRY_SLEEP_SECONDS = 10
LOOP_SLEEP_SECONDS = 10


def load_filenames():
    with INPUT.open() as file:
        filenames = json.load(file)

    if not isinstance(filenames, list) or not all(isinstance(name, str) for name in filenames):
        raise ValueError(f"{INPUT} must contain a JSON array of filenames")

    return filenames


def file_url(filename):
    return BASE_URL + quote(filename)


def tif_file_count():
    return sum(1 for path in OUTPUT_DIR.iterdir() if path.is_file() and path.suffix != ".part")


def download(filename):
    destination = OUTPUT_DIR / filename
    part = destination.with_name(destination.name + ".part")

    if destination.exists() and destination.stat().st_size > 0:
        print(f"skip {filename}")
        return

    request = Request(file_url(filename), headers={"User-Agent": "mk6420-tif-fetcher/1.0"})
    with urlopen(request, timeout=60) as response, part.open("wb") as output:
        shutil.copyfileobj(response, output, length=CHUNK_SIZE)

    part.replace(destination)
    print(f"fetched {filename}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    filenames = load_filenames()

    for filename in filenames:
        while tif_file_count() >= 10:
            time.sleep(LOOP_SLEEP_SECONDS)

        while True:
            try:
                download(filename)
                break
            except Exception as error:
                print(f"error fetching {filename}: {error}; retrying in {RETRY_SLEEP_SECONDS}s")
                time.sleep(RETRY_SLEEP_SECONDS)


if __name__ == "__main__":
    main()
