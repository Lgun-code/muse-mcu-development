# Keil project surgery: building `.uvprojx` / `.uvoptx` that Keil actually opens

The single most expensive lesson in this workflow: **a hand-written Keil project file fails**. The v1 project for STM32F103C8T6 was written from scratch and Keil uVision5 rejected it with `Cannot read project file`, giving no indication of which tag was wrong. The v2 project, rebuilt on an official ST example, was confirmed by the user to open, build and flash. Every project since follows the v2 method.

## The method

1. Take a real, working project file pair from an ST official example for the same chip family (sources below). Do not generate XML from a template you invented.
2. Edit only the items on the surgery checklist. Leave every other byte untouched.
3. Keep both files pure ASCII, LF line endings, no BOM, no XML comments.
4. Validate with `scripts/verify_keil_project.py` and a real GCC build before packaging.

## Verified skeleton sources

| File | Source | Notes |
|---|---|---|
| `Project.uvprojx`, `Project.uvoptx` | GitHub `STMicroelectronics/STM32CubeF1`, `Projects/STM32F103RB-Nucleo/Examples/GPIO/GPIO_IOToggle/MDK-ARM/` | Fetch single files via raw URLs (`scripts/fetch_keil_skeleton.py`); never download the whole Cube zip for this. CubeF1 master HEAD at validation time: `c7656f1`. |
| ARM startup `startup_stm32f103xb.s` | GitHub `STMicroelectronics/cmsis-device-f1` (renamed from `cmsis_device_f1`), `Source/Templates/arm/startup_stm32f103xb.s` | Byte-identical to the file in the verified project. This repo commit `c8e9a4a` is the one STM32CubeF1 v1.8.7 pins. PlatformIO packages contain only the GCC startup variant, never this ARM one. |
| HAL, CMSIS, `system_stm32f1xx.c` | PlatformIO package `framework-stm32cubef1` 1.8.7 (ST's STM32CubeF1 1.8.7) | Copy from `~/.platformio/packages/framework-stm32cubef1/` after the first `pio run`. |

For a different chip, find the same three sources inside that family's Cube repository and CMSIS device repo (for example STM32CubeF4 and cmsis-device-f4 for F4 parts). Do not stretch an F1 skeleton onto an F4 target.

## Why the hand-written v1 failed: the eight structural errors

Keep this list beside you when reviewing any project file you did not build by surgery:

1. **Groups in the wrong place.** v1 used `Project > Groups`. Official structure is `Project > Targets > Target > Groups`. This alone is enough to break the file.
2. **Wrong schema declaration.** v1 used `SchemaVersion 2.0` with `xsi:noNamespaceSchemaLocation="project.xsd"`. Official is `1.1` with `noNamespaceSchemaLocation="project_proj.xsd"` (no `xsi:` prefix on that attribute).
3. **XML comment after the declaration.** v1 put a `<!-- ... -->` block between `<?xml ...?>` and `<Project>`. Official files go straight to `<Project>`.
4. **Missing `<RTE>` section.** v1 had none. Official files carry `<RTE>` (the CMSIS CORE component) at project level.
5. **Target options incomplete and polluted.** v1 forced a compiler with `pCCUsed` and `uAC6` entries (a Keil without that exact AC5 build errors out), while its `TargetCommonOption` had only about 15 children, missing roughly 25 required empty elements the official file carries (`FlashUtilSpec`, `StartupFile`, `FlashDriverDll`, `Cmp`, `Asm`, `Linker`, `TargetStatus`, and more), and invented a `FlashSegment` structure inside `MemoryEnv` that official files do not have.
6. **Wrong DLL, debug and utility tags.** v1 wrote `SimDlgDllName` and `TargetDlgDllName` (official: `SimDlgDll`, `TargetDlgDll`); its `DebugOption` used an `OPTFL` plus `FlashDriverDll` structure instead of official `Simulator` / `Target` / `SimDlls` / `TargetDlls`; in `Utilities`, `Flash2` to `Flash4` were structured blocks instead of plain strings, and `DriverSelection` was `0` instead of `4107` (ST-Link).
7. **`.uvoptx` structure completely different.** v1's root children were `SchemaVersion`, `Header`, `Targets`, so Keil could not find the target at all. Official is `ProjectOpt > Target > TargetName / ToolsetNumber / ToolsetName / TargetOption`. Keil reads the `.uvoptx` together with the `.uvprojx`; one bad file fails the pair.
8. **Minor but real.** v1 used CRLF endings (official LF) and a comma-style `Cpu` memory description instead of the official range style.

## The surgery checklist (the only permitted edits)

Starting from the F103RB Nucleo GPIO_IOToggle skeleton, the verified v2 project changed exactly these things:

- `TargetName` set to the deliverable target name (for example `STM32F103C8T6`), `Device` set to the exact Keil device name (`STM32F103C8`).
- Memory ranges in `Cpu` and the flash driver settings adjusted to the real part: F103C8T6 is Flash 64 KB (`0x8000000` to `0x800FFFF`) and RAM 20 KB. The skeleton's 128 KB flash became 64 KB; RAM was already 20 KB.
- Board-specific defines removed (the skeleton's `USE_STM32F1xx_NUCLEO` define does not belong in a Blue Pill project).
- C/C++ `IncludePath` replaced with the project's own paths. For the reference layout: `..\Core\Inc`, `..\Drivers\STM32F1xx_HAL_Driver\Inc`, `..\Drivers\CMSIS\Include`, `..\Drivers\CMSIS\Device\ST\STM32F1xx\Include`.
- `Define` set to `USE_HAL_DRIVER,STM32F103xB` (density macro matches the chip: `xB` medium density, `xE` high density, and so on).
- Optimisation `Optim` set to `0` (-O0, friendliest for bring-up), `CreateHexFile` set to `1`.
- `ScatterFile` pointed at the project scatter file (for example `.\STM32F103C8T6.sct`).
- `Groups` replaced with the project's real file list. The reference project has 48 referenced files: 7 in Core, 29 in the HAL driver group, 11 in CMSIS, 1 ARM startup file, plus the skeleton's empty `::CMSIS` group kept as-is.
- `.uvoptx` edited the same minimal way: device strings `STM32F103RB` to `STM32F103C8`, flash algorithm `STM32F10x_128` to `STM32F10x_64`, `-FL020000` to `-FL010000`. ST-Link over SWD is kept (`STLink\ST-LINKIII-KEIL_SWO.dll`, flash algorithm `STM32F10x_64.FLM`).
- No forced compiler: no `pCCUsed` anywhere, so the user's default AC5 or AC6 both build the project. HAL 1.8.7 sources compile under both.

## Adapting to another chip

Everything above is a delta on four per-chip facts. Get them right and the method carries over:

| Fact | F103C8T6 (validated) | Where to get it for a new chip |
|---|---|---|
| Keil `Device` name | `STM32F103C8` | The Cube example for the nearest Nucleo or Eval board, or the device pack |
| Flash and RAM ranges | 64 KB at `0x08000000`, 20 KB at `0x20000000` | The chip datasheet, memory map section |
| Density macro | `STM32F103xB` | The CMSIS device header name for the part |
| Device pack | `Keil.STM32F1xx_DFP` 2.4.0 (newer is fine) | Pack Installer, search the family (`STM32F1xx`, `STM32F4xx`, ...) |
| Flash algorithm | `STM32F10x_64.FLM` | Follows the flash size: 64 KB parts use `_64`, 128 KB parts use `_128` |
| PlatformIO board | `bluepill_f103c8` | `pio boards` for the platform, or the Nucleo board id |

Update the scatter file to the same flash and RAM numbers, and the `platformio.ini` defines to the same density macro and `HSE_VALUE`. A mismatch between the Keil memory ranges, the scatter file and the datasheet is a classic silent failure: the project opens, builds, and then flashes to the wrong size or faults at runtime.

## Validation snippet

`scripts/verify_keil_project.py` performs these checks automatically. The minimal manual version:

```bash
python3 -c "
import xml.etree.ElementTree as ET
for f in ['MDK-ARM/<Target>.uvprojx', 'MDK-ARM/<Target>.uvoptx']:
    r = ET.parse(f).getroot()
    print(f, 'root=', r.tag, 'children=', [c.tag for c in r])
"
# Expected: .uvprojx root=Project, children include SchemaVersion, Header, Targets, RTE
#           .uvoptx root=ProjectOpt, children=[Target]
```
