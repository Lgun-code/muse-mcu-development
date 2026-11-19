# Troubleshooting: Keil, PlatformIO and bring-up faults

Work the symptom table first. When the user reports a problem, collect the four items at the end of this file before changing anything; most "it won't open" reports are path or device-pack issues, not project defects.

## Symptom table

| Symptom | Likely cause | Fix |
|---|---|---|
| Keil: `Cannot read project file 'D:\...\....uvprojx'` and the path contains non-ASCII characters or spaces | Keil legacy builds read paths through ANSI APIs and fail on such paths | Move the whole folder to a pure-ASCII short path such as `D:\STM32F103C8T6-Keil\` and reopen |
| Keil: `An error occurred while reading the project file` on a clean ASCII path | The `.uvprojx` or `.uvoptx` structure is wrong (hand-written or damaged in editing) | Do not patch tag by tag. Rebuild by official-skeleton surgery (`keil-project-surgery.md`) and re-validate |
| `pio run` links with `undefined reference to 'main'` | `src_dir` / `include_dir` were placed under `[env:...]`, where PlatformIO 6 silently ignores them, so only framework files compiled | Move both options into the `[platformio]` section (see `templates/platformio.ini`) |
| GCC: duplicate definition of `SystemInit` / `SystemCoreClock` | Both the project's and the framework's `system_stm32f1xx.c` were compiled | Exclude the project's copy in `platformio.ini` via `build_src_filter` (the Keil build still compiles the project's copy) |
| GCC or Keil: `stm32_hal_legacy.h: No such file`, or `LSE_STARTUP_TIMEOUT` undeclared in `stm32f1xx_hal_rcc.c` | The copied HAL set is incomplete, or the trimmed `stm32f1xx_hal_conf.h` lost a define | Copy `Inc/Legacy/stm32_hal_legacy.h` from the framework package into the project, restore the timeout defines in `hal_conf.h`, rerun both verification layers |
| Keil: compiler not found, or a complaint about ARM Compiler 5 | The project forces AC5 (a `pCCUsed` entry survived from somewhere) | Remove the forced compiler so Keil uses its default; deliverable projects built by surgery never contain `pCCUsed`. If the user only has the old v1 package, send the current one instead of debugging v1 |
| Keil: device not found when opening the project | The family device pack is not installed | Pack Installer, search the family (F1: `STM32F1xx`, pack `Keil.STM32F1xx_DFP`) and install; newer pack versions are fine |
| Keil builds, ST-Link connects, but the chip ID or flash size looks wrong | Memory ranges or flash algorithm in the project do not match the physical part (common with C8 versus CB clones and remarked chips) | Check the real flash size with STM32CubeProgrammer, then align `Cpu` ranges, the scatter file and the `.FLM` algorithm with the datasheet values for the actual part |
| Board flashed, serial output present, LED dark | Some Blue Pill clones wire the on-board LED differently, or to a different pin | Trust the serial output first; confirm the LED pin and polarity against the actual board before changing code |
| Board flashed, LED works, no serial output | TX and RX crossed, or the terminal is not at the configured baud rate | PA9 (TX) goes to the adapter's RX and PA10 (RX) to its TX, grounds joined; terminal at 115200 8N1 for the reference demo |
| ST-Link not recognised inside Keil | Debugger selection or port wrong | Options for Target, Debug: Use ST-Link Debugger; in its Settings choose Port SWD; the chip ID (`STM32F103C8` for the reference) should appear |
| PA15, PB3 or PB4 behave oddly as GPIO on F103 | JTAG is still enabled and owns them | The reference MSP disables JTAG and keeps SWD via `__HAL_AFIO_REMAP_SWJ_NOJTAG()`. Keep that call, or use the full SWJ disable only if SWD debugging is not needed |

## The four things to ask for on any failure report

1. The full error text, verbatim or as a screenshot.
2. The Keil version (Help, About uVision).
3. The full path the project was unzipped to.
4. Whether the family device pack is installed.

Do not start a rebuild until these are known. A screenshot of the error plus the path resolves most cases in one round.

## Fallback: build the Keil project by hand (user side)

Use this when a surgically built project still fails on the user's machine. The sources are already verified by the cloud GCC build, so a hand-built project from the same files is sound:

1. In Keil: Project, New uVision Project, saved to a pure-ASCII short path. Select the exact device (reference: `STM32F103C8`).
2. Create three groups: `Core`, `Drivers/<family>_HAL_Driver`, `Drivers/CMSIS`.
3. Add to the groups: all of `Core/Src/*.c`, all of `Drivers/<family>_HAL_Driver/Src/*.c`, `Core/Src/system_<series>.c`, and the ARM startup file from `MDK-ARM/`.
4. Options for Target, C/C++: add the include paths (reference layout: `..\Core\Inc`, `..\Drivers\STM32F1xx_HAL_Driver\Inc`, `..\Drivers\CMSIS\Include`, `..\Drivers\CMSIS\Device\ST\STM32F1xx\Include`) and the defines (`USE_HAL_DRIVER,STM32F103xB` for the reference).
5. Options for Target, Linker: select the project scatter file (reference: `STM32F103C8T6.sct`) as the Scatter File.
6. Options for Target, Debug: ST-Link Debugger, Settings port SWD. Options for Target, Output: tick Create HEX File.
7. F7 to build, F8 to flash.

## Proteus questions

Proteus is paid Windows software published by Labcenter. Current public releases are in the 9.x line. There is no public download for 8.17; holders of a valid licence get older or current builds through their Labcenter account, the in-application update manager, or their reseller. Do not search for unofficial 8.17 downloads, and do not promise Proteus simulation results from the cloud VM, which cannot run it.
