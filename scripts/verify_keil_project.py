#!/usr/bin/env python3
"""verify_keil_project.py - machine-check a generated Keil uVision project.

Keil rejects subtly malformed .uvprojx / .uvoptx files with a bare
"Cannot read project file" and no hint about which tag is wrong. This
validator encodes the structural checks that distinguish the verified
official-skeleton projects from hand-written ones, plus the delivery
hygiene rules (relative paths only, ASCII, LF, no BOM, no XML comments,
every referenced file present on disk).

Usage:
    python3 verify_keil_project.py <project-dir>
    python3 verify_keil_project.py <path-to.uvprojx>

<project-dir> is the folder that contains MDK-ARM/ (the project root).
Exit code 0 means every check passed. Standard library only.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FAILURES = []
NOTES = []


def fail(msg):
    FAILURES.append(msg)
    print(f"FAIL  {msg}")


def ok(msg):
    print(f"PASS  {msg}")


def note(msg):
    NOTES.append(msg)
    print(f"NOTE  {msg}")


def check_raw_hygiene(path: Path):
    before = len(FAILURES)
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(f"{path.name}: has a UTF-8 BOM")
    if b"\r\n" in raw:
        fail(f"{path.name}: contains CRLF line endings (official files use LF)")
    if b"<!--" in raw:
        fail(f"{path.name}: contains an XML comment (official files have none)")
    try:
        raw.decode("ascii")
    except UnicodeDecodeError as exc:
        fail(f"{path.name}: not pure ASCII ({exc})")
    text = raw.decode("ascii", errors="replace")
    for pat, label in [(r"/home/", "unix home path"), (r"[A-Za-z]:\\", "drive-letter path"),
                       (r"\.pio", ".pio build directory")]:
        if re.search(pat, text):
            fail(f"{path.name}: contains forbidden {label} (paths must be project-relative)")
    if len(FAILURES) == before:
        ok(f"{path.name}: ASCII, LF, no BOM, no XML comments, no absolute paths")


def resolve(base: Path, win_path: str) -> Path:
    return (base / win_path.replace("\\", "/")).resolve()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    arg = Path(sys.argv[1]).resolve()
    if arg.suffix == ".uvprojx":
        uvprojx = arg
    else:
        candidates = sorted((arg / "MDK-ARM").glob("*.uvprojx"))
        if not candidates:
            print(f"FAIL  no .uvprojx found under {arg}/MDK-ARM")
            return 1
        uvprojx = candidates[0]
    mdk_dir = uvprojx.parent
    uvoptx = uvprojx.with_suffix(".uvoptx")
    print(f"Project : {uvprojx}")
    print(f"Options : {uvoptx}\n")

    if not uvoptx.exists():
        fail(f"{uvoptx.name} missing next to the .uvprojx")
        return 1

    check_raw_hygiene(uvprojx)
    check_raw_hygiene(uvoptx)

    # ---- .uvprojx structure -------------------------------------------------
    try:
        root = ET.parse(uvprojx).getroot()
    except ET.ParseError as exc:
        fail(f".uvprojx is not well-formed XML: {exc}")
        return 1
    if root.tag != "Project":
        fail(f".uvprojx root is <{root.tag}>, expected <Project>")
    else:
        ok(".uvprojx root is <Project>")

    child_tags = [c.tag for c in root]
    schema = root.findtext("SchemaVersion", default="").strip()
    if schema != "1.1":
        fail(f"SchemaVersion is {schema!r}, expected '1.1' (hand-written files often use 2.0)")
    else:
        ok("SchemaVersion is 1.1")
    if "RTE" not in child_tags:
        fail("<RTE> section missing at project root")
    else:
        ok("<RTE> section present")
    if root.find("Groups") is not None:
        fail("<Groups> sits directly under <Project>; it must be inside Targets > Target")
    groups = root.find("./Targets/Target/Groups")
    if groups is None:
        fail("no Groups found under Targets > Target")
    else:
        ok("Groups nested under Targets > Target")

    tco = root.find("./Targets/Target/TargetOption/TargetCommonOption")
    device = tco.findtext("Device", default="").strip() if tco is not None else ""
    cpu = tco.findtext("Cpu", default="").strip() if tco is not None else ""
    if device:
        ok(f"Device: {device}")
    else:
        fail("TargetCommonOption/Device is empty")
    if cpu:
        note(f"Cpu: {cpu}")

    if root.find(".//pCCUsed") is not None:
        note("pCCUsed present: the project forces a compiler version. "
             "Official-skeleton projects omit it so AC5 and AC6 both work.")

    # Defines and include paths: the C/C++ tab keeps the non-empty pair.
    defines = [d.text.strip() for d in root.iter("Define") if d.text and d.text.strip()]
    if any("USE_HAL_DRIVER" in d for d in defines):
        ok(f"Defines include USE_HAL_DRIVER: {defines}")
    else:
        fail(f"no Define containing USE_HAL_DRIVER found (found: {defines})")

    inc_paths = []
    for ip in root.iter("IncludePath"):
        if ip.text and ip.text.strip() and ";" in ip.text:
            inc_paths = [p.strip() for p in ip.text.split(";") if p.strip()]
    if inc_paths:
        missing_inc = [p for p in inc_paths if not resolve(mdk_dir, p).is_dir()]
        if missing_inc:
            fail(f"include paths that do not exist on disk: {missing_inc}")
        else:
            ok(f"all {len(inc_paths)} include paths exist on disk")
    else:
        note("no multi-entry C/C++ IncludePath found (check the project manually)")

    scatter = root.findtext(".//ScatterFile", default="").strip()
    if scatter:
        if resolve(mdk_dir, scatter).exists():
            ok(f"scatter file exists: {scatter}")
        else:
            fail(f"scatter file referenced but missing: {scatter}")
    else:
        note("no ScatterFile set (Keil will use its default memory layout)")

    # ---- referenced files ----------------------------------------------------
    file_paths = [fp.text.strip() for fp in root.iter("FilePath") if fp.text and fp.text.strip()]
    missing = [p for p in file_paths if not resolve(mdk_dir, p).exists()]
    if missing:
        fail(f"{len(missing)} of {len(file_paths)} referenced files missing on disk: {missing[:8]}")
    else:
        ok(f"all {len(file_paths)} files referenced by the project exist on disk")

    # ---- .uvoptx structure ----------------------------------------------------
    try:
        oroot = ET.parse(uvoptx).getroot()
    except ET.ParseError as exc:
        fail(f".uvoptx is not well-formed XML: {exc}")
        oroot = None
    if oroot is not None:
        if oroot.tag != "ProjectOpt":
            fail(f".uvoptx root is <{oroot.tag}>, expected <ProjectOpt>")
        elif oroot.find("Target") is None:
            fail(".uvoptx has no <Target> child under <ProjectOpt>")
        else:
            ok(".uvoptx root is <ProjectOpt> with a <Target> child")
        raw_opt = uvoptx.read_text(encoding="ascii", errors="replace")
        if "ST-LINKIII-KEIL_SWO" in raw_opt:
            ok("debugger is ST-Link (ST-LINKIII-KEIL_SWO)")
        else:
            note("ST-Link driver string not found in .uvoptx (fine for non-ST-Link debuggers)")

    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} problem(s), {len(NOTES)} note(s))")
        return 1
    print(f"RESULT: PASS ({len(NOTES)} note(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
