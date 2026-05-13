#include "imu.h"
#include <stdint.h>

void IMU_Init(I2C_HandleTypeDef *hi2c, UART_HandleTypeDef *huart) {
    uint8_t chipId;
    HAL_StatusTypeDef ret;

    // TODO: Axis Remapping (map axis of dog to axis of IMU)

    ret = HAL_I2C_Mem_Read(
        hi2c, 
        (BNO055_ADDR << 1), 
        CHIP_ID_REG, 
        I2C_MEMADD_SIZE_8BIT, 
        &chipId, 
        1, 
        100
    );

    if (ret == HAL_OK && chipId == BNO055_ID) {
        if (huart) {
            char msg[64];
            int n = snprintf(msg, sizeof(msg), "Sensor found \r\n");
            HAL_UART_Transmit(huart, (uint8_t*)msg, (uint16_t)n, PCA9685_I2C_TIMEOUT_MS);
        }
    }

    // Write a register command to switch IMU into IMU mode (fusion mode with accelerometer + gyroscope, no magnetometer)
    // OPR_MODE register is 0x3D. IMU Mode is 0x08.
    uint8_t mode = 0x08; 
    HAL_I2C_Mem_Write(
        hi2c, 
        (BNO055_ADDR << 1), 
        0x3D, I2C_MEMADD_SIZE_8BIT, 
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
    yaw   = (double)yaw_raw / 16.0;
    roll  = (double)roll_raw / 16.0;
    pitch = (double)pitch_raw / 16.0;

    orientation->yaw = yaw;
    orientation->roll = roll;
    orientation->pitch = pitch;
}
