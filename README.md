# muse-mcu-development

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Keil](https://img.shields.io/badge/Keil-uVision5-purple.svg)](https://www.keil.com/)
[![PlatformIO](https://img.shields.io/badge/PlatformIO-6.2.0-orange.svg)](https://platformio.org/)
[![STM32CubeF1](https://img.shields.io/badge/STM32CubeF1-HAL%201.8.7-blue.svg)](https://github.com/STMicroelectronics/STM32CubeF1)

**English** | [简体中文](README.zh-CN.md)

An agent skill (plus scripts and a complete reference project) that takes STM32 firmware development from a **bare Linux cloud VM** to a **Keil uVision5 project the user can open on Windows, build with F7 and flash with F8** — without the detours that cost real projects real days.

It exists because the naive path fails in specific, repeatable ways:

- A hand-written `.uvprojx` looks plausible and Keil rejects it with `Cannot read project file`, without saying which tag is wrong.
- PlatformIO silently ignores `src_dir` written in the wrong section, and the build fails at link time with `undefined reference to 'main'`.
- The framework ships two copies of the system file, and compiling both duplicates `SystemInit`.
- The ARM startup file Keil needs is not in the package everyone downloads; only the GCC variant is.
- Keil fails on unzip paths containing non-ASCII characters with the *same* error message as a corrupt project file.

Every one of these is documented in this repository with its cause and its fix, and the workflow is built so a fresh agent never has to rediscover them.

## Validated end to end

Reference target: **STM32F103C8T6 (Blue Pill)**, STM32CubeF1 HAL 1.8.7, HSE 8 MHz to 72 MHz, LED blink plus USART1 counter demo.

| Check | Result (re-measured 2026-11-19 on a fresh VM) |
|---|---|
| Toolchain bootstrap from nothing | PlatformIO Core 6.2.0 in `~/.venvs/pio`, first build downloads `ststm32 20.0.0`, `framework-stm32cubef1 1.8.7`, `toolchain-gccarmnoneeabi 1.70201.0` |
| Layer 1 build (`pio run`) | **SUCCESS** — RAM 232 / 20480 bytes, Flash 6980 / 65536 bytes |
| Layer 2 build (project's own files and `hal_conf.h` only) | Clean compile and link — text 7144, data 120 |
| Keil project validation (`scripts/verify_keil_project.py`) | All checks pass; all 48 referenced files present |
| Keil project on Windows | v2 project confirmed by the user to open, build (F7) and flash (F8, ST-Link SWD) |
| Skeleton fetch (`scripts/fetch_keil_skeleton.py`) | Downloads the 3 official files; ARM startup byte-identical to the verified project's |

## Quickstart

**For an AI agent (Muse and compatible skill runtimes):** install this repository as a skill (copy it into your skills directory; the entry point is `SKILL.md`, the descriptor is `skill.yaml`), then just ask for STM32 firmware. The skill drives everything below.

**For a human following along:**

```bash
# 1. Deploy the cloud toolchain (idempotent, about 10 minutes on a fresh VM)
bash scripts/bootstrap.sh

# 2. Start from the verified reference project
cp -r examples/stm32f103c8t6-bluepill ~/workspace/my-project
cd ~/workspace/my-project

# 3. Build and verify in the cloud
export PATH="$HOME/.venvs/pio/bin:$PATH"
pio run            # expect [SUCCESS] and the RAM/Flash usage lines

# 4. Machine-check the Keil project before delivering it
python3 ../muse_mcu_development/scripts/verify_keil_project.py .
```

Then unzip on Windows to a pure-ASCII path (for example `D:\my-project\`), open `MDK-ARM/*.uvprojx`, install the `Keil.STM32F1xx_DFP` device pack if prompted, F7 to build, F8 to flash.

## How it works

1. **Bootstrap** — PlatformIO in a dedicated virtualenv; the ARM toolchain and ST packages download automatically on first build.
2. **Scaffold from known-good** — never from a blank folder: copy the bundled reference project, or fetch official skeleton files for another chip with `scripts/fetch_keil_skeleton.py`.
3. **Write HAL code** — application logic in `Core/Src`, low-level setup in MSP and interrupt files, patterns in `references/hal-and-code-patterns.md`.
4. **Verify twice in the cloud** — the PlatformIO build, plus a standalone GCC build that uses only the project's own trimmed configuration (this second layer is what catches incomplete HAL copies).
5. **Keil by surgery, never by hand** — official example project files edited only at checklist points (`references/keil-project-surgery.md` lists all eight structural errors of the hand-written attempt), then machine-validated.
6. **Package and hand off** — versioned zip, `OPEN_FIRST.txt`, a README with the real measured build numbers, and exact Windows instructions including the four things to report back when something fails (`references/troubleshooting.md`).

## Repository layout

```text
SKILL.md / skill.yaml     the skill itself (entry point and descriptor)
scripts/
  bootstrap.sh            idempotent toolchain deployment
  fetch_keil_skeleton.py  download the official Keil skeleton and ARM startup files
  verify_keil_project.py  structural and hygiene validation of a Keil project
references/
  keil-project-surgery.md   the v1 failure analysis and the permitted-edits checklist
  hal-and-code-patterns.md  HAL module map, clock/GPIO/UART/TIM/ADC/I2C/SPI patterns, layer-2 build
  troubleshooting.md        symptom table, fallback manual project, report-back list
templates/
  platformio.ini          the fixed cloud-build configuration (three load-bearing settings)
  STM32F103C8T6.sct       scatter file, Flash 64K / RAM 20K
  OPEN_FIRST.txt          first-read file template for deliveries
examples/
  stm32f103c8t6-bluepill/ the complete verified reference project (text files; see its README)
```

## Scope and limits

- The cloud VM cannot run Keil or Proteus (Windows-only; no Wine attempts), cannot flash a board and cannot debug on target. Cloud GCC success plus the file-level validation is strong evidence, and the skill says so in every delivery instead of overselling it.
- Other STM32 families follow the same method with per-chip values (device name, memory ranges, density macro, device pack, flash algorithm) swapped per the table in `references/keil-project-surgery.md`. Only the F103C8T6 path is validated end to end so far.
- ESP32 is a different toolchain and out of scope for this skill.

## License

The skill text, scripts and templates are MIT licensed (see `LICENSE`). The bundled example project contains STMicroelectronics HAL, CMSIS and startup code under ST's and Arm's own licenses; see `NOTICE.md` before redistributing that part.
