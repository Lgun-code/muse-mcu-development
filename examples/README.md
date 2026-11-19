# Bundled example: stm32f103c8t6-bluepill

This is the complete, user-verified v2 reference project for
STM32F103C8T6 on a Blue Pill board: PC13 LED blinking every 500 ms and
USART1 (PA9/PA10, 115200 8N1) printing a counter every second, built
with STM32CubeF1 HAL 1.8.7. Its Keil project was confirmed on Windows
to open in uVision5, build with F7 and flash with F8 over ST-Link.

Copy it as the starting point for new F103C8T6 work instead of
scaffolding from scratch:

```bash
cp -r examples/stm32f103c8t6-bluepill ~/workspace/<your-project>
```

One deliberate difference from the original delivery zip: the compiled
`firmware/STM32F103C8T6.elf` and `.bin` binaries are not committed
(this repository is text-only so it can be mirrored through tools that
reject binaries). The prebuilt `.hex` is included. Regenerate the full
set by running `pio run` in the project root and copying `.elf`,
`.bin` and `.hex` out of `.pio/build/bluepill_f103c8/` into
`firmware/`, exactly as SKILL.md Step 3 describes.
