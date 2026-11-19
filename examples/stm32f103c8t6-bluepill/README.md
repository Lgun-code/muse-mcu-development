# STM32F103C8T6 Keil 工程（Blue Pill）

> **v2（2026-11-19）：已修复 v1 打不开的问题。先看工程根目录的 `OPEN_FIRST.txt`。**
> v1 的 `.uvprojx` 是手写的，结构和 Keil 要求的不一致（Groups 放错了位置、SchemaVersion 不对、
> `.uvoptx` 结构完全错了），Keil 一读就报 `Cannot read project file`。
> v2 的 `.uvprojx` / `.uvoptx` 是用 ST 官方 STM32CubeF1 的 `GPIO_IOToggle` 例子工程
> （`Projects/STM32F103RB-Nucleo/Examples/GPIO/GPIO_IOToggle/MDK-ARM/Project.uvprojx`，
> GitHub `STMicroelectronics/STM32CubeF1`）做骨架重建的，只改了芯片、文件列表、头文件路径等必要内容。
> **另外必须解压到纯英文短路径，例如 `D:\STM32F103C8T6-Keil\`，不要放在桌面、不要放在含中文的路径，**
> Keil uVision5 老版本读中文路径也会直接报 `Cannot read project file`。

芯片：**STM32F103C8T6**，板子：**Blue Pill**，晶振：**8 MHz HSE**，系统时钟：**72 MHz（PLL ×9）**。
库：**STM32CubeF1 HAL 1.8.7**（自包含，见下面“HAL 来源”）。

演示程序（`Core/Src/main.c`，纯 HAL，不用裸寄存器做主要逻辑）：

- **PC13 板载 LED 每 500 ms 闪烁一次**（Blue Pill 的 LED 是低电平点亮，PC13 拉低 = 灯亮）。
- **USART1（PA9 TX / PA10 RX），115200 8N1，每 1 秒打印一次**：
  `Hello STM32F103C8T6` + 计数 `Count: N`。

## 1. 在 Windows 的 Keil 里打开

1. 把整个 `stm32f103c8t6-keil` 文件夹拷到 Windows 电脑上（整个文件夹一起拷，不要只拷 `MDK-ARM`），
   **解压到纯英文短路径，例如 `D:\STM32F103C8T6-Keil\`。不要放在桌面、不要放在含中文的路径、路径不要有空格。**
   错误例子：`D:\桌面\STM32F103C8T6-Keil\...`（含中文，Keil 一定报 `Cannot read project file`）。
2. 双击 **`MDK-ARM/STM32F103C8T6.uvprojx`**，用 Keil uVision5 打开。
3. 工程里所有路径都是相对路径（`..\Core\...`、`..\Drivers\...`），不依赖云电脑的任何绝对路径，换个盘符、换个文件夹都能打开。

## 2. 需要装的东西

- **Keil MDK-ARM（uVision5）**。
- **Device Pack：Keil.STM32F1xx_DFP**（工程里写的是 2.4.0，装更新的版本也可以）。
  打开 Keil 后点工具栏的 **Pack Installer**，搜 `STM32F1xx` 安装；没装的话打开工程时会提示找不到器件。
- **编译器：用 Keil 默认的编译器就行**，优化 **-O0**。v2 的工程没有强制指定 AC5（官方例子骨架本来就不写
  `pCCUsed`），所以不管你的 Keil 默认是 AC5 还是 AC6 都能编，代码和 HAL 两边都兼容，不用改源码。
  v1 强制写了 AC5 V5.06，没装 AC5 的 Keil 会报找不到编译器，v2 已经把这个问题去掉了。

## 3. 编译

按 **F7（Build）**，或者菜单 `Project -> Build Target`。

正常会得到 0 错误 0 警告，输出在 `MDK-ARM/Objects/`，同时生成 `MDK-ARM/Objects/STM32F103C8T6.hex`。
如果 Keil 提示找不到头文件，先确认第 2 步的 Device Pack 已装，再检查整个文件夹是否完整拷过来了。

## 4. 用 ST-Link 烧录

1. ST-Link 接 Blue Pill 的 **SWDIO、SWCLK、GND、3.3V**（工程里已把 JTAG 关掉、只留 SWD，见 `stm32f1xx_hal_msp.c` 里的 `__HAL_AFIO_REMAP_SWJ_NOJTAG()`，所以 PA13/PA14 是 SWD 口，别再当普通 IO 用）。
2. 板子供电，Keil 里点 **Flash -> Download（F8）**，或者点工具栏的下载按钮。
3. 调试用 **Debug -> Start/Stop Debug Session（Ctrl+F5）**，调试器已选好 **ST-Link**。
   如果 Keil 认不到 ST-Link：检查 `Options for Target -> Debug -> Use: ST-Link Debugger`，再点旁边的 **Settings**，确认 **Port 选 SWD**、能看到芯片 ID（`STM32F103C8`）。
4. 不想用 Keil 烧录也可以：`firmware/STM32F103C8T6.hex` 是云端编译好的固件，用 STM32CubeProgrammer / ST-Link Utility 直接烧这个 `.hex` 也行。

## 5. 接线与预期现象

| 信号 | 引脚 | 接法 |
| --- | --- | --- |
| 板载 LED | PC13 | 板子上已接好，不用外接；低电平亮 |
| 串口 TX | PA9 | 接 USB 转串口模块的 RX |
| 串口 RX | PA10 | 接 USB 转串口模块的 TX |
| 地 | GND | 接 USB 转串口模块的 GND |
| 调试 | SWDIO / SWCLK | 接 ST-Link 对应引脚 |

上电烧录后：

- 板载 LED 每 500 ms 亮灭切换一次。
- 串口助手（115200 8N1）每 1 秒收到一次：
  `Hello STM32F103C8T6`，下一行 `Count: 1`、`Count: 2`……一直往上数。
- 如果 LED 不亮但串口有输出：先检查 PC13（有的山寨 Blue Pill 板载 LED 接法不同）；如果串口没输出：检查 PA9/PA10 的 TX/RX 有没有接反、波特率是不是 115200。

## 6. 工程结构

```text
stm32f103c8t6-keil/
├── OPEN_FIRST.txt                先看这个：解压路径要求 + 打不开怎么办
├── README.md                     本说明
├── platformio.ini                云端 GCC 验证用的 PlatformIO 配置（Keil 不用它）
├── Core/
│   ├── Inc/
│   │   ├── main.h
│   │   ├── stm32f1xx_hal_conf.h  HAL 配置（只开了用到的模块，见下）
│   │   └── stm32f1xx_it.h
│   └── Src/
│       ├── main.c                演示程序：LED + 串口
│       ├── stm32f1xx_hal_msp.c   USART1 的 GPIO/时钟/中断配置
│       ├── stm32f1xx_it.c        中断服务函数
│       └── system_stm32f1xx.c    系统时钟初始化（ST 原版）
├── Drivers/                      自包含，不用再装 PlatformIO / CubeMX
│   ├── CMSIS/Include/            core_cm3.h 等 Cortex-M3 内核头文件
│   ├── CMSIS/Device/ST/STM32F1xx/Include/   stm32f1xx.h、stm32f103xb.h
│   └── STM32F1xx_HAL_Driver/
│       ├── Inc/                  只保留用到的 HAL 模块头文件
│       │                         + Inc/Legacy/stm32_hal_legacy.h
│       └── Src/                  只保留用到的 HAL 模块源文件
├── MDK-ARM/
│   ├── STM32F103C8T6.uvprojx    Keil 工程（双击打开它）
│   ├── STM32F103C8T6.uvoptx     Keil 工程选项（ST-Link 调试）
│   ├── STM32F103C8T6.sct        分散加载：Flash 64K @ 0x08000000，RAM 20K @ 0x20000000
│   └── startup_stm32f103xb.s    ARM 版（Keil 用）启动文件
└── firmware/                     云端 GCC 编译好的固件（可直接烧录）
    ├── STM32F103C8T6.elf
    ├── STM32F103C8T6.bin
    └── STM32F103C8T6.hex
```

HAL 只保留了这些模块（`Core/Inc/stm32f1xx_hal_conf.h` 里开的）：`hal`、`hal_rcc`、`hal_gpio`、
`hal_cortex`、`hal_dma`、`hal_flash`、`hal_pwr`、`hal_uart`、`hal_tim`。
其中 `hal_tim` 当前演示程序没直接用到，是按工程要求预留的；`hal_dma` 是 `hal_uart` 的依赖。
`Drivers/STM32F1xx_HAL_Driver/Inc/Legacy/stm32_hal_legacy.h` 是 `stm32f1xx_hal_def.h` 必须包含的文件，也一起带上了。

## 7. 云端 GCC 验证结果（真实跑过的，不是编的）

云电脑：Ubuntu 24.04，PlatformIO Core 6.2.0，`platform = ststm32`，`board = bluepill_f103c8`，
`framework = stm32cube`，工具链 `toolchain-gccarmnoneeabi 1.70201.0`，HAL 包 `framework-stm32cubef1 1.8.7`。

### PlatformIO 编译（`pio run`）

最终结果：**SUCCESS**。

```text
RAM:   [          ]   1.1% (used 232 bytes from 20480 bytes)
Flash: [=         ]  10.7% (used 6980 bytes from 65536 bytes)
========================= [SUCCESS] Took 1.88 seconds =========================
```

`arm-none-eabi-size`：`text 7136 / data 120 / bss 1656`，`.bin` 7256 字节。
固件在 `firmware/` 里（`.elf` / `.bin` / `.hex` 都是这次成功编译的产物）。

### 第一次编译其实失败了，原因和修复都记在这里

第一次 `pio run` 在链接时失败：`undefined reference to 'main'`。
原因是 `platformio.ini` 里把 `src_dir` / `include_dir` 写在了 `[env:bluepill_f103c8]` 下面，
PlatformIO 6 会忽略这两个选项（明确报了 `Warning! Ignore unknown configuration option`），
结果只编译了框架的 HAL，没编译 `Core/Src/main.c`。
修复：把它们移到 `[platformio]` 全局段（见现在的 `platformio.ini`）。之后编译一次通过。

### Keil 工程文件集的独立验证（只用工程里的文件，不用 PlatformIO 的框架）

因为 PlatformIO 编译用的是它自己包里的 HAL 和默认 `hal_conf.h`（全模块开启），
为了证明**工程里这套精简文件在 Keil 的配置下也能编过**，又单独跑了一次直接 GCC 编译：
只用本工程的 `Core/Src/*.c` + `Drivers/.../Src/*.c` + 工程自己的 `stm32f1xx_hal_conf.h`，
启动文件用框架包里的 GCC 版（Keil 工程里没有、也不会引用它）。

结果：**编译 + 链接全部通过**，`text 7140 / data 120 / bss 1656`，`.bin` 7260 字节，
和 PlatformIO 的结果只差 4 个字节（精简版 `hal_conf.h` 的影响）。
这次验证还发现并修了两个真实问题，都已包含在工程里：

1. 缺了 `Drivers/STM32F1xx_HAL_Driver/Inc/Legacy/stm32_hal_legacy.h`（`stm32f1xx_hal_def.h` 要包含它），已补上。
2. 工程的 `stm32f1xx_hal_conf.h` 一开始缺了 `LSE_STARTUP_TIMEOUT` 的定义，`stm32f1xx_hal_rcc.c` 编译报错，已补上。

### `.uvprojx` 校验

用脚本解析了 `MDK-ARM/STM32F103C8T6.uvprojx` 和 `.uvoptx`，结果**通过，0 缺失文件**：
XML 合法；48 个工程引用文件全部在磁盘上存在；无绝对路径（无 `/home/hatch`、无 `C:`、无 `.pio`）；
器件 `STM32F103C8`、Cortex-M3、晶振 8 MHz、Flash 64K / RAM 20K、宏 `USE_HAL_DRIVER,STM32F103xB`、
头文件路径、优化 -O0、ST-Link 调试、分散加载文件 `.\\STM32F103C8T6.sct` 全部检查通过。
（v2 补充校验：`.uvprojx` 根结构与 ST 官方例子一致：`SchemaVersion 1.1`、`<RTE>` 存在、
`Groups` 在 `<Target>` 里面而不是根目录、`<TargetCommonOption>` 子标签顺序与官方一致、
`.uvoptx` 根结构为 `ProjectOpt > Target`、ST-Link 调试器 `STLink\ST-LINKIII-KEIL_SWO.dll`、
Flash 算法 `STM32F10x_64.FLM`、两个文件全 ASCII、无中文、无 BOM、LF 换行、无 XML 注释。）

## 8. HAL 与启动文件来源（没用假文件）

- HAL 驱动、CMSIS 头文件、`system_stm32f1xx.c`：来自 PlatformIO 下载的
  `framework-stm32cubef1 1.8.7`（即 ST 官方 STM32CubeF1 1.8.7），原样复制，只删了没用到的模块。
- ARM 版启动文件 `MDK-ARM/startup_stm32f103xb.s`：PlatformIO 的包里**只有 GCC 版启动文件，没有 ARM 版**，
  所以是从 ST 官方仓库 `STMicroelectronics/cmsis_device_f1` 取的；
  已核对过：该仓库当前提交 `c8e9a4a4f16b6d2cb2a2083cbe5161025280fb22`
  正是 STM32CubeF1 **v1.8.7** 标签锁定的 CMSIS 设备库提交，版本一致。
  文件头明确写着 `STM32F103xB Devices vector table for MDK-ARM toolchain`，
  复位后调用 `SystemInit` 再进 `__main`。
- GCC 版启动文件只在云端验证时用框架包里的那份，**没有**放进工程、Keil 工程也不引用它；
  Keil 工程只引用 ARM 版 `startup_stm32f103xb.s`，两者没有混用。
- 工程里的 `system_stm32f1xx.c` 和框架包里的那份是同一个 ST 源文件，只差换行符（LF / CRLF）；
  PlatformIO 编译时用的是框架包里的那份（它自带），Keil 编译时用的是工程里这份，
  所以 `platformio.ini` 里把工程的 `system_stm32f1xx.c` 从 GCC 编译里排除了，避免 `SystemInit` 重复定义。

## 9. 云电脑做不了的事（先说清楚）

- **云电脑跑不了 Keil 和 Proteus**，它们都是 Windows 软件；本工程是在云电脑上写好、编好、校验好，
  拿到 Windows 上用 Keil 打开、编译、烧录。Keil 里的最终编译没有在云电脑上跑过，
  云端验证的是同一套源码 + 同一个 HAL 版本的 GCC 编译（第 7 节），不能 100% 等同于 Keil 编译，
  但文件、配置、宏定义、启动文件都已按 Keil 的要求备齐并校验过。
- **云电脑接不到实物板子**，不能直接把程序烧进 STM32，也不能做真机在线调试；
  烧录和调试要在 Windows + ST-Link 上做（第 4 节）。
- 云端复现 GCC 验证：装好 PlatformIO 后，在工程根目录跑 `pio run` 即可
  （云电脑上的 PlatformIO 装在 `~/.venvs/pio` 的虚拟环境里，工程里不带 `.pio` 构建目录，
  跑 `pio run` 会自动重新生成）。

## 10. 如果 v2 还是打不开（备用方案）

先确认三件事，再报障：

1. 路径是纯英文短路径吗（例如 `D:\STM32F103C8T6-Keil\...`）？含中文、含空格的路径先换掉再试一次。
2. Keil 是什么版本？`Help -> About uVision` 里看版本号，连同完整报错原文一起发回来。
3. `Keil.STM32F1xx_DFP` 装了吗？没装的话 Pack Installer 里搜 `STM32F1xx` 安装。

备用方案——在 Keil 里新建空工程（源码本身没问题，云端 GCC 已编译通过）：

1. Keil 里 `Project -> New uVision Project`，存在纯英文短路径，器件选 `STM32F103C8`。
2. 右键 Target 1 新建三个 Group：`Core`、`Drivers/STM32F1xx_HAL_Driver`、`Drivers/CMSIS`，
   按第 6 节的分组把 `Core/Src/*.c`、`Drivers/STM32F1xx_HAL_Driver/Src/*.c`、
   `Core/Src/system_stm32f1xx.c` 和 `MDK-ARM/startup_stm32f103xb.s` 加进去
   （`.h` 文件不用加，加 `.c` 和 `.s` 就够了）。
3. `Options for Target -> C/C++ -> Include Paths` 填这 4 条：
   `..\Core\Inc`、`..\Drivers\STM32F1xx_HAL_Driver\Inc`、
   `..\Drivers\CMSIS\Include`、`..\Drivers\CMSIS\Device\ST\STM32F1xx\Include`；
   `Define` 填 `USE_HAL_DRIVER,STM32F103xB`；`Linker` 里勾上 `Use Memory Layout from Target Dialog`，
   或者把 `MDK-ARM/STM32F103C8T6.sct` 选为 Scatter File。
4. `Options for Target -> Debug -> Use: ST-Link Debugger`，`Settings` 里 Port 选 SWD。
5. F7 编译，F8 烧录。现象见第 5 节。
