# Orion Firmware

FreeRTOS firmware for the STM32F401 handling all real-time control.

## FreeRTOS Tasks

| Task | Priority | Description |
|:-----|:---------|:------------|
| `controlTask` | Realtime | IK, gait execution, body posture, IMU-based stabilization |
| `rxCommTask` | High | DMA UART RX — parses packed binary commands from Jetson |
| `txCommTask` | Normal | Sends telemetry to Jetson (IMU, battery voltages, joint angles) |
| `batteryTask` | Low+1 | Polls INA3221 for 3-rail battery voltages |
| `imuTask` | Low | Reads BNO055 orientation (roll, pitch, yaw) |

Shared state protected by `cmdMutex`, `imuMutex`, and `batteryMutex`. FreeRTOS automatic priority inheritance prevents priority inversion.

## Command Protocol (Jetson → STM32)

48-byte packet received over UART at up to 100 Hz via DMA:

| Bytes | Fields | Description |
|:------|:-------|:------------|
| 0–1 | `0xAA 0x55` | Frame header |
| 2 | `cmd_type` (u8) | `NORMAL`, `RESET`, `WAVE`, `HEEL`, `DANCE`, `EXTRAS`, `EYES`, `BOOTUP` |
| 3–6 | `lin_x` | Linear velocity X (float) |
| 7–10 | `lin_y` | Linear velocity Y (float) |
| 11–14 | `ang_z` | Angular velocity Z / yaw rate (float) |
| 15–18 | `roll` | Body roll offset (float, degrees) |
| 19–22 | `pitch` | Body pitch offset (float, degrees) |
| 23–26 | `yaw` | Body yaw offset (float, degrees) |
| 27–30 | `z_offset` | Body height offset (float, mm) |
| 31–34 | `x_offset` | Body forward translation (float, mm) |
| 35–38 | `y_offset` | Body lateral translation (float, mm) |
| 39–42 | `pivot_x` | Rotation pivot X (float) |
| 43–46 | `pivot_y` | Rotation pivot Y (float) |
| 47 | XOR checksum | XOR over payload bytes 2–46 |

## Telemetry Protocol (STM32 → Jetson)

99-byte packet sent over UART at 10 Hz via DMA:

| Bytes | Fields | Description |
|:------|:-------|:------------|
| 0–1 | `0xAA 0x55` | Frame header |
| 2–13 | `roll`, `pitch`, `yaw` | IMU orientation (3 × float, degrees) |
| 14–49 | `bus_voltage_V[0..8]` | INA3221 bus voltages across all 9 channels (9 × float, volts) |
| 50–97 | Joint angles (FL, FR, BL, BR) × (hip, femur, tibia) | 12 joint angles (12 × float, degrees) |
| 98 | XOR checksum | XOR over all payload bytes (bytes 2–97) |

## Key Source Files

| File | Description |
|:-----|:------------|
| `freertos.c` | Task definitions, DMA UART parser, command dispatch, telemetry TX |
| `LegIK.c/h` | 3-DOF per-leg IK — hip, femur, tibia angles from Cartesian foot position |
| `BodyIK.c/h` | 6-DOF body posture — translation + roll/pitch/yaw with configurable pivot |
| `LegMotion.c/h` | Gait algorithms (trot, wave, sine step), servo actuation, pose definitions |
| `ServoConfig.h` | Per-servo calibrated center offsets and PCA9685 channel mappings |
| `imu.c/h` | BNO055 IMU driver |
| `ina3221.c/h` | INA3221 triple-channel voltage monitor driver |
| `pca9685.c/h` | PCA9685 16-channel PWM servo driver |