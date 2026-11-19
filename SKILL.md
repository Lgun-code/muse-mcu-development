# Muse MCU development: STM32 + Keil with cloud GCC verification

Take an STM32 firmware task from a bare Linux Muse VM to a Keil uVision5 project the user can open on Windows, build with F7 and flash to the board with F8 (ST-Link, SWD). The cloud VM writes the code, verifies it with GCC and generates the Keil files. Flashing and on-target debugging happen only on the user's Windows machine.

Fully validated end to end on **STM32F103C8T6 (Blue Pill, STM32CubeF1 HAL 1.8.7)**. The workflow, scripts and checklists generalise to other STM32 chips; per-chip values that change are listed in `references/keil-project-surgery.md`.

## Iron rules (each one is a pitfall already paid for)

- **Never hand-write `.uvprojx` / `.uvoptx`.** Keil rejects subtly wrong project files with `Cannot read project file` and does not say which tag is wrong. Always start from a real ST official example project and edit it surgically (Step 4). The full v1-failure diff list is in `references/keil-project-surgery.md`.
- **Never claim a build passed without running it in this session.** Run `pio run` (and the standalone check in Step 3) after every change and quote the real numbers in the delivery README. A plan, a similar past result, or "the code looks right" is not verification.
- **Never try to run Keil or Proteus in the cloud VM.** Both are Windows-only. Do not attempt Wine installs. State this boundary to the user up front instead of discovering it mid-task.
- **Pure ASCII short paths everywhere.** Cloud paths and the user's Windows path alike: no Chinese characters, no spaces. A Chinese path alone makes Keil report `Cannot read project file`. Project files themselves are ASCII only, LF line endings, no BOM, no XML comments.
- **Iterate on the verified project, never restart per feature.** New peripherals are added to the existing project with the four-way sync in Step 5.

## Step 0 — Intake (one short round of questions, then work)

- Confirm: exact chip (for example STM32F103C8T6), board (Blue Pill, Nucleo, custom), HSE crystal frequency, peripherals and behaviour wanted, debugger (default ST-Link over SWD).
- Default when the user does not specify: STM32F103C8T6 on Blue Pill, HSE 8 MHz, SYSCLK 72 MHz, HAL (not bare registers for application logic), Keil uVision5 deliverable.
- Ask about Proteus only if the user raises it. Proteus is paid Windows software. There is no public download for old versions such as 8.17; it comes through a Labcenter account, the in-app update manager, or a reseller with a valid licence. Do not hunt for 8.17 download links.

## Step 1 — Deploy the toolchain (fresh VM to ready, about 10 minutes)

- Run the bundled bootstrap script. It is idempotent and safe to re-run:

```bash
bash scripts/bootstrap.sh
```

- What it does: checks `python3` and host `gcc`, creates `~/.venvs/pio` (never install PlatformIO into the system Python), installs PlatformIO Core (validated 6.2.0), and prints the versions it found.
- The first `pio run` in a project downloads the rest automatically. Expect these packages (validated 2026-11-19): `platform ststm32 20.0.0`, `framework-stm32cubef1 1.8.7`, `toolchain-gccarmnoneeabi 1.70201.0` (arm-none-eabi-gcc 7.2.1). They land in `~/.platformio/`. Never copy `~/.platformio` or a project's `.pio` directory into a delivery package; both regenerate on demand.
- A fresh VM has none of this: no `arm-none-eabi-gcc`, no PlatformIO, no QEMU, no Wine. Always run the bootstrap check instead of assuming tools exist.
- Success looks like: `pio --version` prints a version and the script ends with `BOOTSTRAP OK`.

## Step 2 — Scaffold the project (start from known-good, never from blank)

- For STM32F103C8T6, copy the bundled reference project and rename it for the task. It is the user-verified v2 project: self-contained HAL and CMSIS, Keil files built by official-skeleton surgery, demo firmware (PC13 LED blink at 500 ms, USART1 115200 printing a counter every second):

```bash
cp -r examples/stm32f103c8t6-bluepill ~/workspace/<project-name>
```

- For another STM32 chip, assemble the same layout from official sources only:
  - HAL and CMSIS come from the matching PlatformIO framework package after the first `pio run` (for F1 that is `~/.platformio/packages/framework-stm32cubef1/`). Copy only the modules the project uses, plus `Inc/Legacy/stm32_hal_legacy.h`, which `stm32f1xx_hal_def.h` requires.
  - The ARM (Keil) startup file is **not** in the PlatformIO package, which ships only the GCC variant. Fetch the ARM variant and the Keil skeleton with `python3 scripts/fetch_keil_skeleton.py --chip <chip>` (see `references/keil-project-surgery.md` for the source repos and commits).
  - Never mix the GCC and ARM startup files. The Keil project references the ARM one only.
- Keep the validated layout: `Core/Inc`, `Core/Src`, `Drivers/CMSIS`, `Drivers/<HAL_Driver>`, `MDK-ARM/` (Keil project, options, scatter file, ARM startup), `firmware/` (cloud-built `.elf` / `.bin` / `.hex`), `platformio.ini` at the root (cloud verification only), `README.md` and `OPEN_FIRST.txt` at the root.
- Copy `templates/platformio.ini` for the cloud build. Its three non-obvious settings are load-bearing and commented in the file: `src_dir` and `include_dir` live in the `[platformio]` section (PlatformIO 6 silently ignores them under `[env:...]` and the link then fails with `undefined reference to 'main'`), `build_src_filter` excludes the project's own `system_stm32f1xx.c` (the framework ships an identical copy; compiling both duplicates `SystemInit`), and the defines `USE_HAL_DRIVER`, `STM32F103xB`, `HSE_VALUE=8000000` are mandatory.

## Step 3 — Write code and verify in the cloud (two layers, both required)

- Write application code in `Core/Src/main.c` with HAL APIs. Follow the structure of the reference `main.c`: `HAL_Init()`, `SystemClock_Config()`, one `MX_<Peripheral>_Init()` per peripheral, non-blocking `HAL_GetTick()` scheduling in the main loop instead of long `HAL_Delay` chains when more than one periodic task exists.
- Put low-level setup where CubeMX would: GPIO, clocks and NVIC for a peripheral belong in its `HAL_<PERIPH>__MspInit()` in `stm32f1xx_hal_msp.c`, interrupt handlers in `stm32f1xx_it.c`. On F103 keep `__HAL_AFIO_REMAP_SWJ_NOJTAG()` in `HAL_MspInit()` so PA13 and PA14 stay SWD-only for ST-Link.
- Clock recipe for the reference board: HSE 8 MHz on, PLL source HSE, PLL multiplier 9, SYSCLK 72 MHz, AHB divide 1, APB1 divide 2, APB2 divide 1, Flash latency 2. Other boards: scale the multiplier and latency to the chip's limits and state the resulting SYSCLK in the README.
- Code patterns for GPIO, UART, timers and PWM, ADC, I2C and SPI, plus the HAL module map, are in `references/hal-and-code-patterns.md`.
- Verify layer 1, the PlatformIO build:

```bash
cd ~/workspace/<project-name>
export PATH="$HOME/.venvs/pio/bin:$PATH"
pio run
```

- The reference demo's expected result: `RAM 232 of 20480 bytes`, `Flash 6980 of 65536 bytes`, `[SUCCESS]`. Different code gives different numbers; what matters is `SUCCESS` in this session, with the numbers recorded for the README.
- Verify layer 2, the standalone check: compile once more using **only** the project's own files (its trimmed `stm32f1xx_hal_conf.h`, its copied HAL sources, the framework's GCC startup file). This catches what layer 1 cannot, because layer 1 builds against the framework's full default `hal_conf.h`. Layer 2 is how the two real defects `missing stm32_hal_legacy.h` and `missing LSE_STARTUP_TIMEOUT` were found. A worked command line is in `references/hal-and-code-patterns.md`.
- Copy the built `.elf`, `.bin` and `.hex` from `.pio/build/<board>/` into `firmware/` before packaging.

## Step 4 — Generate or update the Keil project (surgery, then machine-check)

- Read `references/keil-project-surgery.md` before touching any `.uvprojx` or `.uvoptx`. It contains the skeleton sources, the exact list of permitted edits (target name, device, memory ranges, defines, include paths, scatter file, file groups, debugger), and the eight structural mistakes that made the hand-written v1 project unreadable.
- Non-negotiables from that list: `SchemaVersion` 1.1 with a `<RTE>` section present, `Groups` nested inside `Targets > Target`, no forced compiler version (no `pCCUsed`, so the user's default AC5 or AC6 both work), `DriverSelection` 4107 and the ST-Link driver `STLink\ST-LINKIII-KEIL_SWO.dll` for ST-Link targets, optimisation `-O0` and `CreateHexFile` on for deliverables.
- After any edit, run the validator. Every check must pass before packaging:

```bash
python3 scripts/verify_keil_project.py ~/workspace/<project-name>
```

- The validator parses both XML files, confirms the root structures, checks that every file referenced by the project exists on disk, and rejects absolute paths, non-ASCII bytes, BOMs, CRLF endings and XML comments.

## Step 5 — Add a peripheral (four-way sync, every time)

- Do all four, in this order, then repeat both verification layers from Step 3:
  1. Enable the module in `Core/Inc/stm32f1xx_hal_conf.h` (add the `HAL_<X>_MODULE_ENABLED` define and the matching include block).
  2. Copy the module's `.c` and `.h` files from the framework package into `Drivers/<HAL_Driver>/Src` and `Inc`.
  3. Add the new source files to the Keil project's `Groups` by editing the surgically-built `.uvprojx` (Step 4 rules), and add any user driver files under `Core` the same way.
  4. Write the `MX_` init, the MSP init and the interrupt handler, then re-run `pio run`, the standalone check and `verify_keil_project.py`.
- Skipping step 1 or 2 is the usual cause of `unknown type name` and missing-symbol errors that only appear in one of the two build paths. The two-layer verification exists to catch exactly this.

## Step 6 — Package and deliver

- Bump the version on every delivery (v2, v3, and so on). Never overwrite the previous package; the user may need to roll back.
- Delete `.pio` from the project folder before zipping. Zip the whole project folder, then list the archive and confirm the file count matches the folder (`unzip -l`).
- The package must contain: the full project, `OPEN_FIRST.txt` (start from `templates/OPEN_FIRST.txt`), a `README.md` stating the chip, clock, wiring, expected behaviour, the real cloud verification numbers from this session, and the manual fallback (build a fresh Keil project by hand from the same sources, detailed in `references/troubleshooting.md`).
- Deliver large packages as a download link the user can copy as plain text, not as a chat attachment they cannot open on a phone.

## Step 7 — Windows handoff (give the user these exact instructions)

- Unzip to a pure-ASCII short path such as `D:\STM32F103C8T6-Keil\`. Never the Desktop, never a path with Chinese characters or spaces.
- Open `MDK-ARM\<Target>.uvprojx` in Keil uVision5. Install the device pack when prompted (for F1: `Keil.STM32F1xx_DFP` via Pack Installer, search `STM32F1xx`). Use the default compiler; the project forces neither AC5 nor AC6.
- Press F7 to build (expect 0 errors, 0 warnings, hex in `MDK-ARM/Objects/`). Connect ST-Link to SWDIO, SWCLK, GND and 3.3 V, power the board, press F8 to flash. Debug with Ctrl+F5; in debugger settings the port must be SWD.
- Alternative flashing path: burn `firmware/<Target>.hex` directly with STM32CubeProgrammer.
- When something fails, do not accept "it won't open" as a report. Ask for four things: the full error text or a screenshot, the Keil version (Help, About uVision), the full unzip path, and whether the device pack is installed. Then work `references/troubleshooting.md`.

## Boundaries

- The cloud VM cannot flash a board, cannot debug on target, and cannot run Keil or Proteus. Cloud GCC success is strong evidence, not a 100 percent substitute for the Keil build; say so in the delivery README, with the file-level checks that were run.
- ESP32 is a different toolchain (ESP-IDF or Arduino via PlatformIO, no Keil). Treat it as a separate task and confirm the user's choice before scaffolding anything for it.
- Do not invent download links, version numbers, or build results. Every version and number in this skill was measured on 2026-11-19; re-measure on the current VM and report what you actually saw.

## Available connectors

- [GitHub](/opt/hatch/connectors/github/CONNECTOR.md) for fetching official ST example projects and startup files, and for publishing finished projects or this skill.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.
