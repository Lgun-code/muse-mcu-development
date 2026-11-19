#!/usr/bin/env python3
"""fetch_keil_skeleton.py - download the official Keil skeleton files.

Keil project files must never be hand-written (Keil rejects subtly wrong
ones with "Cannot read project file"). This script fetches the three
official files a new project is built from, so no one has to download
the several-hundred-MB STM32Cube zip just for two XML files:

  1. Project.uvprojx / Project.uvoptx from the ST STM32CubeF1 example
     Projects/STM32F103RB-Nucleo/Examples/GPIO/GPIO_IOToggle/MDK-ARM/
     (GitHub STMicroelectronics/STM32CubeF1, master)
  2. The ARM (MDK-ARM) startup file for the requested density from
     STMicroelectronics/cmsis-device-f1 (renamed from cmsis_device_f1),
     Source/Templates/arm/startup_<density>.s

All URLs were verified live on 2026-11-19, and the downloaded
startup_stm32f103xb.s was byte-identical to the one in the user-verified
reference project. PlatformIO framework packages ship only the GCC
startup variant, which is why the ARM one is fetched separately.

Usage:
    python3 fetch_keil_skeleton.py --out <dir> [--density stm32f103xb]

Densities present in cmsis-device-f1: stm32f103xb (validated end to end),
stm32f103x6, stm32f103xe, stm32f103xg (startup verified to exist; the
F103RB skeleton is shared and the surgery step adjusts device and
memory ranges). For other STM32 series, find the matching Nucleo or
Eval example inside that series' STM32Cube repository and pass the two
project files with --uvprojx-url / --uvoptx-url, plus --startup-url.
Standard library only.
"""

import argparse
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CUBE_F1_EXAMPLE = (
    "https://raw.githubusercontent.com/STMicroelectronics/STM32CubeF1/master/"
    "Projects/STM32F103RB-Nucleo/Examples/GPIO/GPIO_IOToggle/MDK-ARM/"
)
CMSIS_DEVICE_F1 = (
    "https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-f1/master/"
    "Source/Templates/arm/"
)
KNOWN_DENSITIES = ["stm32f103xb", "stm32f103x6", "stm32f103xe", "stm32f103xg"]


def fetch(url: str, dest: Path) -> None:
    print(f"GET {url}")
    data = None
    last_exc = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "muse-skill-fetch"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            break
        except Exception as exc:  # network paths vary; retry, then fall back to curl
            last_exc = exc
            print(f"  attempt {attempt + 1} failed: {exc}")
            time.sleep(2)
    if data is None:
        if shutil.which("curl") is None:
            raise SystemExit(f"FAIL: urllib failed ({last_exc}) and curl is not available")
        print("  falling back to curl")
        proc = subprocess.run(["curl", "-fsSL", "--max-time", "60", url],
                              capture_output=True)
        if proc.returncode != 0:
            raise SystemExit(f"FAIL: curl failed for {url}: {proc.stderr.decode(errors='replace')}")
        data = proc.stdout
    if len(data) < 200 or data.lstrip().startswith(b"404"):
        raise SystemExit(f"FAIL: unexpected content from {url} ({len(data)} bytes)")
    dest.write_bytes(data)
    print(f"  -> {dest} ({len(data)} bytes)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output directory (created if needed)")
    ap.add_argument("--density", default="stm32f103xb", help="startup density (default stm32f103xb)")
    ap.add_argument("--uvprojx-url", default=None, help="override skeleton .uvprojx URL")
    ap.add_argument("--uvoptx-url", default=None, help="override skeleton .uvoptx URL")
    ap.add_argument("--startup-url", default=None, help="override ARM startup .s URL")
    args = ap.parse_args()

    if args.density not in KNOWN_DENSITIES and not args.startup_url:
        print(f"FAIL: density {args.density} not in {KNOWN_DENSITIES}; "
              "pass --startup-url for other chips.")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fetch(args.uvprojx_url or (CUBE_F1_EXAMPLE + "Project.uvprojx"), out / "Project.uvprojx")
    fetch(args.uvoptx_url or (CUBE_F1_EXAMPLE + "Project.uvoptx"), out / "Project.uvoptx")
    fetch(args.startup_url or (CMSIS_DEVICE_F1 + f"startup_{args.density}.s"),
          out / f"startup_{args.density}.s")
    print("\nSkeleton ready. Next: rename the project files for your target and apply")
    print("the surgery checklist in references/keil-project-surgery.md, then run")
    print("scripts/verify_keil_project.py on the assembled project.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
