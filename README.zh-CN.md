# muse-mcu-development

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Keil](https://img.shields.io/badge/Keil-uVision5-purple.svg)](https://www.keil.com/)
[![PlatformIO](https://img.shields.io/badge/PlatformIO-6.2.0-orange.svg)](https://platformio.org/)
[![STM32CubeF1](https://img.shields.io/badge/STM32CubeF1-HAL%201.8.7-blue.svg)](https://github.com/STMicroelectronics/STM32CubeF1)

[English](README.md) | **简体中文**

一个 Agent Skill（附脚本和一份完整参考工程），把 STM32 固件开发从**一台空白的 Linux 云电脑**一路做到**用户能在 Windows 上用 Keil uVision5 打开、F7 编译、F8 烧录的工程**，并且把这条路上真实踩过的坑全部绕开。

它存在的原因是：朴素做法会在几个固定的地方反复失败：

- 手写的 `.uvprojx` 看起来像模像样，Keil 直接报 `Cannot read project file`，还不告诉你哪个标签错了。
- PlatformIO 把写错段落的 `src_dir` 静默忽略，链接时报 `undefined reference to 'main'`。
- 框架包和工程里各有一份系统文件，两份都编就 `SystemInit` 重复定义。
- Keil 需要的 ARM 版启动文件不在大家下载的那个包里，包里只有 GCC 版。
- 解压路径带中文时 Keil 报的错，和工程文件损坏时一模一样。

以上每一个坑在本仓库里都有成因和修法，整个流程的设计目标就是让新接手的 Agent 不必再踩一遍。

## 已全程验证

参考目标：**STM32F103C8T6（Blue Pill）**，STM32CubeF1 HAL 1.8.7，HSE 8 MHz 倍频到 72 MHz，演示程序为 LED 闪烁加 USART1 计数打印。

| 检查项 | 结果（2026-11-19 在全新虚拟机上复测） |
|---|---|
| 工具链从零部署 | PlatformIO Core 6.2.0 装入 `~/.venvs/pio`，首次编译自动下载 `ststm32 20.0.0`、`framework-stm32cubef1 1.8.7`、`toolchain-gccarmnoneeabi 1.70201.0` |
| 第一层验证（`pio run`） | **SUCCESS**，RAM 232 / 20480 字节，Flash 6980 / 65536 字节 |
| 第二层验证（只用工程自身文件和 `hal_conf.h`） | 编译链接干净通过，text 7144，data 120 |
| Keil 工程校验（`scripts/verify_keil_project.py`） | 全部通过，工程引用的 48 个文件无一缺失 |
| Windows 端 Keil | v2 工程已由用户确认能打开、F7 编译、F8 经 ST-Link（SWD）烧录 |
| 骨架抓取（`scripts/fetch_keil_skeleton.py`） | 3 个官方文件下载成功，ARM 启动文件与已验证工程里的逐字节一致 |

## 快速开始

**给 AI Agent（Muse 及兼容的 skill 运行时）：** 把本仓库装成 skill（拷进 skills 目录，入口是 `SKILL.md`，描述文件是 `skill.yaml`），之后直接提 STM32 固件需求即可，skill 会驱动下面全部流程。

**给跟着手动做的人：**

```bash
# 1. 部署云端工具链（幂等，全新虚拟机约 10 分钟）
bash scripts/bootstrap.sh

# 2. 从已验证的参考工程起步
cp -r examples/stm32f103c8t6-bluepill ~/workspace/my-project
cd ~/workspace/my-project

# 3. 云端编译验证
export PATH="$HOME/.venvs/pio/bin:$PATH"
pio run            # 预期 [SUCCESS] 并打印 RAM/Flash 用量

# 4. 交付前机器校验 Keil 工程
python3 ../muse_mcu_development/scripts/verify_keil_project.py .
```

然后在 Windows 上解压到纯英文路径（例如 `D:\my-project\`），打开 `MDK-ARM/*.uvprojx`，按提示装 `Keil.STM32F1xx_DFP` 器件包，F7 编译，F8 烧录。

## 工作原理

1. **部署**：PlatformIO 装进独立虚拟环境，ARM 工具链和 ST 的包在首次编译时自动下载。
2. **从已知能用的工程起步**：永远不从空文件夹开始。要么拷贝仓库自带的参考工程，要么用 `scripts/fetch_keil_skeleton.py` 为其他芯片抓官方骨架文件。
3. **写 HAL 代码**：应用逻辑在 `Core/Src`，底层配置在 MSP 和中断文件里，常用外设写法见 `references/hal-and-code-patterns.md`。
4. **云端双层验证**：PlatformIO 编译之外，再做一次只用工程自身精简配置的独立 GCC 编译。HAL 文件拷贝不全这类问题只有第二层能抓出来。
5. **Keil 工程只做手术、绝不手写**：拿官方例子工程当骨架，只改清单允许的项（`references/keil-project-surgery.md` 列全了手写 v1 的八个结构性错误），改完机器校验。
6. **打包交付**：版本号递增的压缩包，带 `OPEN_FIRST.txt`，README 里写本轮真实测得的编译数字，附 Windows 端确切操作说明和故障时要回传的四项信息（`references/troubleshooting.md`）。

## 仓库结构

```text
SKILL.md / skill.yaml     skill 本体（入口与描述文件）
scripts/
  bootstrap.sh            幂等的工具链部署脚本
  fetch_keil_skeleton.py  下载官方 Keil 骨架与 ARM 启动文件
  verify_keil_project.py  Keil 工程的结构与规范校验
references/
  keil-project-surgery.md   v1 失败分析和允许修改的清单
  hal-and-code-patterns.md  HAL 模块表、时钟/GPIO/UART/TIM/ADC/I2C/SPI 写法、第二层验证
  troubleshooting.md        故障对照表、手工建工程备用方案、回传清单
templates/
  platformio.ini          修好坑的云端编译配置（三个关键设置）
  STM32F103C8T6.sct       分散加载文件，Flash 64K / RAM 20K
  OPEN_FIRST.txt          交付时「先看这个」文件模板
examples/
  stm32f103c8t6-bluepill/ 完整的已验证参考工程（纯文本文件，见其 README）
```

## 范围与边界

- 云电脑跑不了 Keil 和 Proteus（Windows 专用，不尝试 Wine），接不到板子，不能烧录也不能真机调试。云端 GCC 通过加文件级校验是强证据，但 skill 要求每次交付都如实说明这一点，不夸大。
- 其他 STM32 系列走同一套方法，按 `references/keil-project-surgery.md` 的表替换每颗芯片不同的值（器件名、内存区间、密度宏、器件包、Flash 算法）。目前只有 F103C8T6 这条线全程验证过。
- ESP32 是另一套工具链，不在本 skill 范围内。

## 许可证

Skill 文本、脚本和模板为 MIT 许可证（见 `LICENSE`）。自带参考工程里包含 STMicroelectronics 的 HAL、CMSIS 和启动代码，其再分发遵循 ST 与 Arm 各自的许可证，见 `NOTICE.md`。
