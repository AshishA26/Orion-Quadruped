#ifndef PCA9685_H
#define PCA9685_H

#include "stm32f4xx_hal.h"
#include <stdint.h>
#include <i2c.h>

void PCA9685_Init(I2C_HandleTypeDef *hi2c);
HAL_StatusTypeDef PCA9685_SetPWM_us(uint8_t channel, uint16_t microseconds);
HAL_StatusTypeDef PCA9685_SetPWM(uint8_t channel, uint16_t on, uint16_t off);
HAL_StatusTypeDef PCA9685_SetPWMFreq(I2C_HandleTypeDef *hi2c, float freq_hz);

#endif // PCA9685_H