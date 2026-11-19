# HAL module map and code patterns (STM32F1, STM32CubeF1 HAL 1.8.7)

The clock, GPIO and UART patterns below are lifted from the user-verified reference project (`examples/stm32f103c8t6-bluepill/`). The timer, ADC, I2C and SPI patterns are standard HAL patterns for this HAL version: they must pass both cloud verification layers before delivery, and their on-target behaviour can only be confirmed on the user's board.

## The HAL module map

A trimmed project carries only the modules it uses. Enabling a peripheral is always the four-way sync from SKILL.md Step 5. This table is the shopping list for step 1 and 2 of that sync (paths are inside the framework package and mirrored inside the project under `Drivers/STM32F1xx_HAL_Driver/`):

| Peripheral or need | `hal_conf.h` define | Files to copy (Inc and Src) | Notes |
|---|---|---|---|
| Core (always) | `HAL_MODULE_ENABLED` | `stm32f1xx_hal`, `hal_cortex`, `hal_flash`, `hal_pwr`, `hal_rcc` (+ `_ex` where present) | Plus `Inc/Legacy/stm32_hal_legacy.h`, required by `hal_def.h` |
| GPIO and EXTI | `HAL_GPIO_MODULE_ENABLED` | `hal_gpio`, `hal_gpio_ex` | EXTI lines ride on GPIO on F1; implement `HAL_GPIO_EXTI_Callback` in user code |
| DMA | `HAL_DMA_MODULE_ENABLED` | `hal_dma`, `hal_dma_ex` | Dependency of UART and ADC DMA modes; harmless to always include |
| UART / USART | `HAL_UART_MODULE_ENABLED` | `hal_uart` | MSP does pin mux, clocks and NVIC (see reference `stm32f1xx_hal_msp.c`) |
| Timers, PWM, input capture | `HAL_TIM_MODULE_ENABLED` | `hal_tim`, `hal_tim_ex` | The reference project pre-enables this module |
| ADC | `HAL_ADC_MODULE_ENABLED` | `hal_adc`, `hal_adc_ex` | F1 needs `HAL_ADCEx_Calibration_Start()` before first conversion |
| I2C | `HAL_I2C_MODULE_ENABLED` | `hal_i2c` | Pins are open-drain alternate function (`GPIO_MODE_AF_OD`) |
| SPI | `HAL_SPI_MODULE_ENABLED` | `hal_spi` | `hal_conf.h` carries `USE_SPI_CRC` (default 1); set 0 if CRC is unused and size matters |
| RTC | `HAL_RTC_MODULE_ENABLED` | `hal_rtc`, `hal_rtc_ex` | Needs LSE or LSI clock setup in RCC oscillator config |
| IWDG / WWDG | `HAL_IWDG_MODULE_ENABLED` / `HAL_WWDG_MODULE_ENABLED` | `hal_iwdg` / `hal_wwdg` | Feed the watchdog in the main loop, never in an interrupt |

When copying from the framework package, copy the `.h` and the matching `.c` together, then add the `.c` to the Keil project groups. A header without its source links fine under GCC layer 1 (the framework supplies the object) and fails only in the standalone layer or in Keil, which is why both layers exist.

## Clock pattern (verified, Blue Pill)

HSE 8 MHz crystal, PLL times 9, SYSCLK 72 MHz. Full code lives in the reference `main.c` (`SystemClock_Config`). The load-bearing values:

- `OscillatorType = RCC_OSCILLATORTYPE_HSE`, `HSEState = RCC_HSE_ON`, `HSEPredivValue = RCC_HSE_PREDIV_DIV1`, `HSIState = RCC_HSI_ON`
- `PLL.PLLState = RCC_PLL_ON`, `PLL.PLLSource = RCC_PLLSOURCE_HSE`, `PLL.PLLMUL = RCC_PLL_MUL9`
- `SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK`, AHB divide 1, APB1 divide 2, APB2 divide 1, `FLASH_LATENCY_2`
- Every `HAL_RCC_*Config` return value checked against `HAL_OK` with `Error_Handler()` on failure

APB1 at divide 2 means timer clocks on APB1 double back to 72 MHz (the F1 timer clock rule); remember this when computing PWM frequencies.

## GPIO pattern (verified)

- Enable the port clock first (`__HAL_RCC_GPIOC_CLK_ENABLE()`), set the output level before configuring the pin to avoid a glitch, then `HAL_GPIO_Init` with `GPIO_MODE_OUTPUT_PP`, `GPIO_NOPULL`, `GPIO_SPEED_FREQ_LOW` for LEDs.
- Blue Pill's on-board LED is on PC13 and is **active low**: pin low means lit. The reference toggles it every 500 ms using `HAL_GetTick()` deltas, not `HAL_Delay`, so the UART task keeps its own 1 s cadence in the same loop.
- Button input with interrupt: configure the pin as `GPIO_MODE_IT_FALLING` with `GPIO_PULLUP`, enable the `EXTI` IRQ in the MSP or init code, implement `HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)` for the logic, and keep the handler itself (`EXTI15_10_IRQHandler` and friends) in `stm32f1xx_it.c` calling `HAL_GPIO_IRQHandler`.

## UART pattern (verified)

- Handle: `UART_HandleTypeDef huart1` with `Instance = USART1`, 115200, 8 bits, 1 stop bit, no parity, TX and RX, no flow control, oversampling 16.
- All pin and clock work is in `HAL_UART_MspInit` (PA9 AF push-pull high speed for TX, PA10 input for RX, USART1 clock, NVIC priority 0 and IRQ enabled). The IRQ handler in `stm32f1xx_it.c` only calls `HAL_UART_IRQHandler(&huart1)`.
- Blocking print: format with `snprintf` into a stack buffer and `HAL_UART_Transmit(&huart1, buf, len, 100)`. For continuous reception, use `HAL_UART_Receive_IT` one byte at a time and re-arm inside `HAL_UART_RxCpltCallback`.

## Timer PWM pattern

Example: TIM3 channel 1 on PA6, 1 kHz PWM at 72 MHz timer clock.

- Enable the module (map above) and the TIM3 and GPIOA clocks in `HAL_TIM_PWM_MspInit`, with PA6 as `GPIO_MODE_AF_PP`.
- `htim3.Init`: `Prescaler = 71` (72 MHz to 1 MHz), `CounterMode = TIM_COUNTERMODE_UP`, `Period = 999` (1 MHz to 1 kHz), `ClockDivision = DIV1`.
- `HAL_TIM_PWM_ConfigChannel` with `OCMode = TIM_OCMODE_PWM1`, `Pulse` set to the duty in counts (500 is 50 percent), `OCPolarity = TIM_OCPOLARITY_HIGH`.
- Start with `HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1)`; change duty at runtime with `__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, value)`.

## ADC pattern

Example: ADC1 channel 0 on PA0, single conversion by polling.

- Enable the module, then in the MSP set the ADC clock prescaler (`RCC_ADCPCLK2_DIV6` gives 12 MHz from 72 MHz, inside the 14 MHz F1 limit), ADC1 and GPIOA clocks, PA0 as `GPIO_MODE_ANALOG`.
- `hadc1.Init`: `ScanConvMode = DISABLE`, `ContinuousConvMode = DISABLE`, `DataAlign = RIGHT`, `NbrOfConversion = 1`.
- Configure the channel (`ADC_CHANNEL_0`, rank 1, `ADC_SAMPLETIME_55CYCLES_5`), run `HAL_ADCEx_Calibration_Start(&hadc1)` once (F1-specific; skipping it is a classic source of offset readings), then per reading: `HAL_ADC_Start`, `HAL_ADC_PollForConversion(&hadc1, 10)`, `HAL_ADC_GetValue`.

## I2C pattern

Example: read a register from a sensor at 7-bit address `0x68` (the MPU-6050 pattern).

- Enable the module; MSP sets the peripheral clock and configures both pins as `GPIO_MODE_AF_OD` with pull-ups (external pull-ups still required on the board).
- `hi2c1.Init`: `ClockSpeed = 400000` (or 100000 for bring-up), `DutyCycle = I2C_DUTYCYCLE_2`, `OwnAddress1 = 0`, `AddressingMode = I2C_ADDRESSINGMODE_7BIT`.
- Register access: `HAL_I2C_Mem_Read(&hi2c1, 0x68 << 1, reg, I2C_MEMADD_SIZE_8BIT, buf, len, 100)` and the matching `HAL_I2C_Mem_Write`. HAL takes the address already shifted left by one.
- Probe first with `HAL_I2C_IsDeviceReady(&hi2c1, 0x68 << 1, 3, 100)` and print the result over UART before building logic on top of a bus that may be miswired.

## SPI pattern

Example: SPI1 master, PA5 SCK, PA7 MOSI, PA6 MISO, software chip select on PA4.

- Enable the module; MSP sets clocks and alternate-function push-pull pins, PA4 as a normal output driven by user code.
- `hspi1.Init`: `Mode = SPI_MODE_MASTER`, `Direction = SPI_DIRECTION_2LINES`, `DataSize = SPI_DATASIZE_8BIT`, `CLKPolarity = SPI_POLARITY_LOW`, `CLKPhase = SPI_PHASE_1EDGE` (mode 0; match the slave's datasheet), `NSS = SPI_NSS_SOFT`, `BaudRatePrescaler = SPI_BAUDRATEPRESCALER_16`, `FirstBit = SPI_FIRSTBIT_MSB`.
- Transfer: pull CS low, `HAL_SPI_TransmitReceive(&hspi1, tx, rx, len, 100)`, CS high. Keep the whole exchange inside one CS assertion.

## Standalone verification (layer 2)

Layer 1 (`pio run`) builds against the framework's full default `hal_conf.h`, so it cannot catch a broken trimmed project configuration. Layer 2 compiles the project's own files with the project's own `hal_conf.h`. Run it after any `hal_conf.h` or driver-set change:

This exact command was re-run and verified on a fresh VM on 2026-11-19:

```bash
# Paths after the first pio run on this VM (adjust if versions differ)
TC="$HOME/.platformio/packages/toolchain-gccarmnoneeabi/bin"
FW="$HOME/.platformio/packages/framework-stm32cubef1"
P="$HOME/workspace/<project-name>"
STARTUP=$(find "$FW" -path "*Templates/gcc/startup_stm32f103xb.S" | head -1)
LD=$(find "$HOME/.platformio/platforms/ststm32" -name "stm32f103x8.ld" | head -1)

"$TC/arm-none-eabi-gcc" -mcpu=cortex-m3 -mthumb -Os -ffunction-sections -fdata-sections \
  -DUSE_HAL_DRIVER -DSTM32F103xB -DHSE_VALUE=8000000 \
  -I"$P/Core/Inc" -I"$P/Drivers/STM32F1xx_HAL_Driver/Inc" \
  -I"$P/Drivers/CMSIS/Include" -I"$P/Drivers/CMSIS/Device/ST/STM32F1xx/Include" \
  "$P"/Core/Src/*.c "$P"/Drivers/STM32F1xx_HAL_Driver/Src/*.c \
  "$STARTUP" -T"$LD" --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections \
  -o /tmp/standalone.elf
"$TC/arm-none-eabi-size" /tmp/standalone.elf
```

Notes that matter:

- The framework's GCC startup file ends in a capital `.S` (`startup_stm32f103xb.S`); a lowercase find pattern silently matches nothing.
- Do not add `-nostartfiles`: newlib then fails the link with undefined `_init` and `_sbrk`. The `--specs=nano.specs --specs=nosys.specs` pair is what resolves the syscall stubs.
- Without `-Os -ffunction-sections -fdata-sections` the link still succeeds but `text` balloons (measured 24004 instead of about 7000); size comparisons are only meaningful with the flags above.
- `Core/Src` includes `system_stm32f1xx.c` here on purpose: layer 2 is the Keil file set, which does compile it. The duplicate-definition problem belongs to layer 1 only and is handled by the `platformio.ini` filter.
- If `find` returns no linker script, list `$HOME/.platformio/platforms/ststm32/ldscripts/` and pick the script matching the part (flash and RAM sizes are in its name or header). Do not invent one.
- Measured result for the reference demo firmware with this command: `text 7144, data 120, bss 120`, binary 7264 bytes. The `bss` figure is not comparable to the layer 1 build (the PlatformIO linker script accounts stack reservation outside `.bss`); what matters is a clean compile and link with the project's own configuration, and a `text` in the same range as layer 1 (7136 for the reference).
