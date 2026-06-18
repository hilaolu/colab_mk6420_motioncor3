#!/usr/bin/env python3
import json
import subprocess
import time
from pathlib import Path


INPUT = Path("tif.json")
TIF_DIR = Path("tif")
OUTPUT_DIR = Path("output")
GAIN = Path("K319040035GainRefx1m3kv300.mrc")
WAIT_SECONDS = 10
MAX_TIF_FILES = 5


def load_filenames():
    with INPUT.open() as file:
        filenames = json.load(file)

    if not isinstance(filenames, list) or not all(isinstance(name, str) for name in filenames):
        raise ValueError(f"{INPUT} must contain a JSON array of filenames")

    return filenames


def wait_for_tif(filename):
    tif_path = TIF_DIR / filename
    while not tif_path.exists():
        print(f"waiting for {tif_path}; sleeping {WAIT_SECONDS}s")
        time.sleep(WAIT_SECONDS)
    return tif_path


def run_motioncor3(tif_path):
    output_path = OUTPUT_DIR / f"{tif_path.stem}.mrc"
    command = [
        "MotionCor3",
        "-InTiff",
        str(tif_path),
        "-OutMrc",
        str(output_path),
        "-Gain",
        str(GAIN),
        "-PixSize",
        "0.415",
        "-FmDose",
        "1.04",
        "-kV",
        "300",
        "-Gpu",
        "0",
        "-OutStar",
        "1",
        "-FtBin",
        "2.00",
    ]

    print("running " + " ".join(command))
    result=subprocess.run(command)
    if(result.returncode):
        print(f"{tif_path} failed!")
    return output_path


def trim_oldest_tif_if_needed():
    tif_files = [
        path
        for path in TIF_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in (".tif", ".tiff")
    ]
    if len(tif_files) <= MAX_TIF_FILES:
        return False

    oldest = min(tif_files, key=lambda path: path.stat().st_mtime)
    oldest.unlink()
    print(f"trimmed oldest tif {oldest}")
    return True


def cleanup_after_run(output_path):
    keep_path = output_path.with_name(f"{output_path.stem}_DW.mrc")

    for path in output_path.parent.glob(f"{output_path.stem}*"):
        if path == keep_path:
            continue

        s=str(path)

        if s.endswith("txt") or s.endswith("star"):
            continue
        if path.is_file():
            path.unlink()

    print(f"kept {keep_path}; deleted other outputs for {output_path.stem}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    if not GAIN.exists():
        raise FileNotFoundError(f"gain file not found: {GAIN}")

    for filename in load_filenames():
        tif_path = wait_for_tif(filename)
        output_path = run_motioncor3(tif_path)
        cleanup_after_run(output_path)

        trim_oldest_tif_if_needed()


if __name__ == "__main__":
    main()
