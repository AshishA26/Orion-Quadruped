#include "imu.h"
#include <stdint.h>

void IMU_Init(I2C_HandleTypeDef *hi2c, UART_HandleTypeDef *huart) {
    uint8_t chipId;
    HAL_StatusTypeDef ret;

    // Test connection
    ret = HAL_I2C_Mem_Read(
        hi2c, 
        (BNO055_ADDR << 1), 
        CHIP_ID_REG, 
        I2C_MEMADD_SIZE_8BIT, 
        &chipId, // Chip id is returned from the read function
        1, 
        100
    );
    if (ret != HAL_OK || chipId != BNO055_ID) {
        return; // IMU not found or wrong chip ID
    }
    if (huart) {
        char msg[64];
        int n = snprintf(msg, sizeof(msg), "Sensor found \r\n");
        HAL_UART_Transmit(huart, (uint8_t*)msg, (uint16_t)n, PCA9685_I2C_TIMEOUT_MS);
    }
    
    // Axis Remapping (map axis of dog to axis of IMU)
    uint8_t axis_remap_config = AXIS_REMAP_CONFIG;
    uint8_t axis_remap_sign = AXIS_REMAP_SIGN;
    HAL_I2C_Mem_Write(
        hi2c, 
        (BNO055_ADDR << 1), 
        AXIS_MAP_CONFIG_ADDR, 
        I2C_MEMADD_SIZE_8BIT, 
        &axis_remap_config, 
        1, 
        100
    );
    HAL_I2C_Mem_Write(
        hi2c, 
        (BNO055_ADDR << 1), 
        AXIS_MAP_SIGN_ADDR, 
        I2C_MEMADD_SIZE_8BIT, 
        &axis_remap_sign, 
        1, 
        100
    );

    // Write a register command to switch IMU into IMU mode 
    // (fusion mode with accelerometer + gyroscope, no magnetometer)
    uint8_t mode = IMU_MODE; 
    HAL_I2C_Mem_Write(
        hi2c, 
        (BNO055_ADDR << 1), 
        OPERATION_MODE_REG_ADDR, 
        I2C_MEMADD_SIZE_8BIT, 
        &mode, 
        1, 
        100
    );
    osDelay(20);
}

void IMU_ReadOrientation(I2C_HandleTypeDef *hi2c, IMU_OrientationTypeDef *orientation) {
    uint8_t buffer[6];
    int16_t yaw_raw, roll_raw, pitch_raw;
    int16_t yaw, roll, pitch;

    // Read 6 bytes starting from EUL_Heading_LSB (0x1A)
    HAL_I2C_Mem_Read(
        hi2c, 
        (BNO055_ADDR << 1), 
        EUL_Heading_LSB,
        I2C_MEMADD_SIZE_8BIT, 
        buffer, 
        6, 
        100
    );
    
    // Combine LSB and MSB
    yaw_raw   = (int16_t)((buffer[1] << 8) | buffer[0]);
    roll_raw  = (int16_t)((buffer[3] << 8) | buffer[2]);
    pitch_raw = (int16_t)((buffer[5] << 8) | buffer[4]);

    // Scale the data (16 ticks per degree)
    yaw   = (float)yaw_raw / 16.0f;
    roll  = (float)roll_raw / 16.0f;
    pitch = (float)pitch_raw / 16.0f;

    orientation->yaw = yaw;
    orientation->roll = roll;
    orientation->pitch = pitch;
}
