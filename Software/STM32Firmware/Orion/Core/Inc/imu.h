#ifndef IMU_H
#define IMU_H

#include "i2c.h"
#include "main.h"
#include "stm32f4xx_hal_i2c.h"
#include "stm32f4xx_hal_uart.h"
#include "stm32f4xx_hal_def.h"
#include "cmsis_os.h"

#define BNO055_ADDR 0x28
#define CHIP_ID_REG 0x00
#define BNO055_ID 0xA0
#define EUL_Heading_LSB 0x1A

typedef struct {
    double yaw;
    double roll;
    double pitch;
} IMU_OrientationTypeDef;

void IMU_Init(I2C_HandleTypeDef *hi2c, UART_HandleTypeDef *huart);
void IMU_ReadOrientation(I2C_HandleTypeDef *hi2c, IMU_OrientationTypeDef *orientation);

#endif // IMU_H