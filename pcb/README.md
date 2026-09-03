# PCB Design Files

KiCad projects for Orion's custom multi-layer PCBs.

## Boards

### [`Orion-Control-Board/`](./Orion-Control-Board/)
Houses compute and sensor interfacing.
- STM32F401 compute module
- BNO055 IMU
- PCA9685 16-channel PWM servo driver (I2C)
- Multiple I2C buses with LTC4311 active termination
- Extensive test pads and debug headers

### [`Orion-Power-Board/`](./Orion-Power-Board/)
Handles all power distribution.
- Raw Li-ion battery input and distribution
- INA3221 triple-channel voltage monitoring (front servos, rear servos, Jetson)
- High-current servo actuation lines
- Battery alarm system

### [`datasheets/`](./datasheets/)
Reference datasheets for key components: STM32F401, BNO055, PCA9685, INA3221, LTC4311, JST eXH connectors, Jetson Orin Nano carrier board, wire ampacity references.