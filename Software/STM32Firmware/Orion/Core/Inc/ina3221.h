#ifndef INA3221_H
#define INA3221_H

#include "i2c.h"
#include "main.h"
#include "stm32f4xx_hal_i2c.h"
#include "stm32f4xx_hal_uart.h"
#include "stm32f4xx_hal_def.h"
#include "cmsis_os.h"

#define INA3221_NUM_DEVICES  3
#define INA3221_CHANNELS_PER_DEVICE 3
#define INA3221_TOTAL_CHANNELS (INA3221_NUM_DEVICES * INA3221_CHANNELS_PER_DEVICE) // 9

typedef struct {
    float bus_voltage_V[INA3221_TOTAL_CHANNELS];   // 9 bus voltages in volts
    float shunt_voltage_mV[INA3221_TOTAL_CHANNELS]; // 9 shunt voltages in mV (for current calc)
} INA3221_ReadingsTypeDef;

HAL_StatusTypeDef INA3221_Init(I2C_HandleTypeDef *hi2c, UART_HandleTypeDef *huart_debug);
HAL_StatusTypeDef INA3221_ReadAll(I2C_HandleTypeDef *hi2c, INA3221_ReadingsTypeDef *readings);

#endif // INA3221_H