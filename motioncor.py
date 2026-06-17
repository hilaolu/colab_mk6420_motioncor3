#!/usr/bin/env python3
import shutil
import subprocess
import time
from pathlib import Path


TIFS_DIR = Path("tifs")
OUT_DIR = Path("out")
RESULT_DIR = Path("result")
GAIN = Path("K319040035GainRefx1m3kv300.mrc")
WAIT_SECONDS = 10


def next_tif():
    while True:
        tif_files = sorted(
            path
            for path in TIFS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in (".tif", ".tiff")
        )
        if tif_files:
            return tif_files[0]

        print(f"no tif files in {TIFS_DIR}; sleeping {WAIT_SECONDS}s")
        time.sleep(WAIT_SECONDS)


def run_motioncor3(tif_path):
    output_path = OUT_DIR / f"{tif_path.stem}.mrc"
    command = [
        "./MotionCor3/MotionCor3",
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
        "-FtBin",
        "2.00",
    ]

    print("running " + " ".join(command))
    result = subprocess.run(command)
    if result.returncode:
        raise RuntimeError(f"{tif_path} failed with exit code {result.returncode}")

    return output_path


def collect_results(stem):
    for path in OUT_DIR.glob(f"{stem}*"):
        keep = path.is_file() and (
            path.name.endswith("_DW.mrc") or path.suffix.lower() == ".txt"
        )
        if keep:
            target = RESULT_DIR / path.name
            shutil.copy2(path, target)
            print(f"copied {path} to {target}")

    for path in OUT_DIR.glob(f"{stem}*"):
        if path.is_file():
            path.unlink()
            print(f"removed {path}")


def main():
    TIFS_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)
    if not GAIN.exists():
        raise FileNotFoundError(f"gain file not found: {GAIN}")

    while True:
        tif_path = next_tif()
        try:
            run_motioncor3(tif_path)
            collect_results(tif_path.stem)
            tif_path.unlink()
            print(f"removed processed tif {tif_path}")
        except Exception as exc:
            print(f"failed to process {tif_path}: {exc}; sleeping {WAIT_SECONDS}s")
            time.sleep(WAIT_SECONDS)


if __name__ == "__main__":
    main()
