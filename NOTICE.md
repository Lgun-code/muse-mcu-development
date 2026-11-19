# NOTICE

This repository combines two kinds of material under different terms.

## Original material (MIT)

The skill text (`SKILL.md`), the scripts in `scripts/`, the reference
documents in `references/`, the templates in `templates/`, and the
user-code files of the example project (`Core/Src/main.c`,
`Core/Src/stm32f1xx_hal_msp.c`, `Core/Src/stm32f1xx_it.c` and the
matching headers as delivered) are original work released under the
MIT License in `LICENSE`.

## Third-party material in `examples/stm32f103c8t6-bluepill/`

The example project is a working STM32 firmware project and therefore
contains files that originate from STMicroelectronics and Arm:

- `Drivers/STM32F1xx_HAL_Driver/` — STM32CubeF1 HAL drivers,
  (c) STMicroelectronics, distributed by ST under the BSD-3-Clause
  license (see the copyright headers in each file).
- `Drivers/CMSIS/` including `Drivers/CMSIS/Device/ST/STM32F1xx/` —
  CMSIS core and device files, (c) Arm Limited and
  STMicroelectronics, under the Apache License 2.0 and ST terms as
  stated in each file's header.
- `Core/Src/system_stm32f1xx.c` — (c) STMicroelectronics.
- `MDK-ARM/startup_stm32f103xb.s` — (c) STMicroelectronics,
  from the `cmsis-device-f1` repository.
- `MDK-ARM/STM32F103C8T6.uvprojx` and `.uvoptx` — derived by editing
  the GPIO_IOToggle example project files from ST's STM32CubeF1
  repository, (c) STMicroelectronics and Keil.

These files keep their original copyright headers, which are the
authoritative license statements for them. If you redistribute the
example project, keep those headers intact and comply with the
respective licenses. The MIT License in this repository does not
relicense ST's or Arm's code.
