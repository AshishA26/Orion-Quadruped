# STM32 Firmware for Orion

Custom STM32F401 firmware for Orion's real-time low-level control.

## Projects

### [`Orion/`](./Orion/) — Main Firmware
FreeRTOS firmware with CMake + STM32CubeIDE. Handles IK, gaits, IMU stabilization, and UART comms with the Jetson. → [Detailed README](./Orion/README.md)

### [`Orion-Controls/`](./Orion-Controls/) — Legacy
Earlier PlatformIO-based firmware from initial development. Superseded by `Orion/`.

---

## Setup

- Install [CMake](https://cmake.org/download/)
- Install VSCode extension: `STM32CubeIDE for VSCode`

## Initial Project Configuration
- Create a Project using `STM32CubeMX`.     
    - Set project type to "CMake"
- Open generated folder in VSCode
- Then follow STM32 Extension's guide:
    - In the STM32 Extension, click `Setup STM32Cube Project(s)`