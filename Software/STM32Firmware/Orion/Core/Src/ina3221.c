// Core/Src/ina3221.c
#include "ina3221.h"
#include <stdint.h>
#include <string.h>

// I2C addresses for the 3 INA3221 devices (from your scan: 0x41, 0x42, 0x43)
static const uint8_t ina3221_addrs[INA3221_NUM_DEVICES] = { 0x41, 0x42, 0x43 };

// Bus voltage registers for each of the 3 channels within one INA3221
static const uint8_t bus_voltage_regs[INA3221_CHANNELS_PER_DEVICE] = { 0x02, 0x04, 0x06 };

// Manufacturer ID register — should read 0x5449 ("TI")
#define INA3221_REG_MANUFACTURER_ID  0xFE

HAL_StatusTypeDef INA3221_Init(I2C_HandleTypeDef *hi2c, UART_HandleTypeDef *huart_debug) {
    HAL_StatusTypeDef status;
    
    for (int i = 0; i < INA3221_NUM_DEVICES; i++) {
        uint8_t buf[2];
        status = HAL_I2C_Mem_Read(
            hi2c,
            (ina3221_addrs[i] << 1),
            INA3221_REG_MANUFACTURER_ID,
            I2C_MEMADD_SIZE_8BIT,
            buf, 2, 100
        );
        
        uint16_t mfr_id = (buf[0] << 8) | buf[1];
        
        if (huart_debug) {
            char msg[64];
            int n;
            if (status == HAL_OK && mfr_id == 0x5449) {
                n = snprintf(msg, sizeof(msg), "INA3221 @ 0x%02X OK\r\n", ina3221_addrs[i]);
            } else {
                n = snprintf(msg, sizeof(msg), "INA3221 @ 0x%02X FAIL (0x%04X)\r\n", ina3221_addrs[i], mfr_id);
            }
            HAL_UART_Transmit(huart_debug, (uint8_t*)msg, (uint16_t)n, 100);
        }
        
        if (status != HAL_OK) return status;
    }
    
    // Default config (0x7127) is fine: all channels enabled, continuous mode
    return HAL_OK;
}

HAL_StatusTypeDef INA3221_ReadAll(I2C_HandleTypeDef *hi2c, INA3221_ReadingsTypeDef *readings) {
    HAL_StatusTypeDef status;
    
    for (int dev = 0; dev < INA3221_NUM_DEVICES; dev++) {
        for (int ch = 0; ch < INA3221_CHANNELS_PER_DEVICE; ch++) {
            uint8_t buf[2];
            status = HAL_I2C_Mem_Read(
                hi2c,
                (ina3221_addrs[dev] << 1),
                bus_voltage_regs[ch],
                I2C_MEMADD_SIZE_8BIT,
                buf, 2, 100
            );
            
            if (status != HAL_OK) return status;
            
            // Bus voltage: 16-bit register, upper 13 bits are data (shift right 3)
            // LSB = 8 mV
            int16_t raw = (int16_t)((buf[0] << 8) | buf[1]);
            raw >>= 3; // Keep upper 13 bits
            
            int idx = dev * INA3221_CHANNELS_PER_DEVICE + ch;
            readings->bus_voltage_V[idx] = (float)raw * 0.008f; // 8 mV per LSB
        }
    }
    
    return HAL_OK;
}
