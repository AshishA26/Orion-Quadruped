/**
 * pca9685.c
 *
 * Minimal PCA9685 driver (HAL I2C)
 *
 * Usage:
 *  - Place this file in Core/Src and the companion header in Core/Inc.
 *  - Include `pca9685.h` where needed.
 *  - Call `PCA9685_Init(&hi2c1)` (pass the HAL I2C handle).
 *  - Use `PCA9685_SetPWM_us(channel, microseconds)` to set servo pulses.
 *
 * Safety notes:
 *  - HAL blocking I2C calls are used; call from a FreeRTOS task (not an ISR).
 *  - Test with servos powered/disconnected as appropriate to avoid mechanical movement.
 */

#include "pca9685.h"

/* PCA9685 register definitions (from datasheet / Adafruit library) */
#define PCA9685_ADDR_7BIT   0x40
#define PCA9685_ADDR        (PCA9685_ADDR_7BIT << 1)   /* HAL expects 8-bit address */
#define PCA9685_MODE1       0x00
#define PCA9685_PRESCALE    0xFE
#define PCA9685_LED0_ON_L   0x06

/* Default oscillator used by Adafruit library; matches your PlatformIO code */
#define PCA9685_OSC_CLOCK_HZ 27000000UL



/* Internal I2C handle used by driver; set during init */
static I2C_HandleTypeDef *pca_hi2c = NULL;

/* ---------- Helper low-level operations ---------- */

/* Write single byte to PCA9685 register */
static HAL_StatusTypeDef pca_write8(uint8_t reg, uint8_t val)
{
    if (!pca_hi2c) return HAL_ERROR;
    return HAL_I2C_Mem_Write(pca_hi2c, PCA9685_ADDR, reg, I2C_MEMADD_SIZE_8BIT, &val, 1, PCA9685_I2C_TIMEOUT_MS);
}

/* Read single byte from PCA9685 register */
static HAL_StatusTypeDef pca_read8(uint8_t reg, uint8_t *out)
{
    if (!pca_hi2c || !out) return HAL_ERROR;
    return HAL_I2C_Mem_Read(pca_hi2c, PCA9685_ADDR, reg, I2C_MEMADD_SIZE_8BIT, out, 1, PCA9685_I2C_TIMEOUT_MS);
}

/* ---------- Public API ---------- */

/**
 * PCA9685_Init
 *  - Stores the I2C handle and performs a soft reset (MODE1=0).
 *  - Then sets a default PWM frequency (50 Hz) suitable for servos.
 */
void PCA9685_Init(I2C_HandleTypeDef *hi2c)
{
    if (!hi2c) return;
    pca_hi2c = hi2c;

    /* Reset MODE1 to 0 (normal mode) */
    uint8_t mode = 0x00;
    (void)HAL_I2C_Mem_Write(pca_hi2c, PCA9685_ADDR, PCA9685_MODE1, I2C_MEMADD_SIZE_8BIT, &mode, 1, PCA9685_I2C_TIMEOUT_MS);

    /* Default to 50 Hz for servos */
    (void)PCA9685_SetPWMFreq(hi2c, 50.0f);
}

/**
 * PCA9685_SetPWMFreq
 *  - Sets the PWM frequency by writing PRESCALE register.
 *  - Uses the formula from datasheet: prescale = round(osc/(4096*freq)) - 1
 *  - Returns HAL_OK on success, HAL_ERROR on bus error.
 */
HAL_StatusTypeDef PCA9685_SetPWMFreq(I2C_HandleTypeDef *hi2c, float freq_hz)
{
    if (!hi2c) return HAL_ERROR;
    pca_hi2c = hi2c;

    if (freq_hz < 1.0f) freq_hz = 1.0f;
    if (freq_hz > 3500.0f) freq_hz = 3500.0f; /* safe clamp */

    float prescaleval = ((float)PCA9685_OSC_CLOCK_HZ / (4096.0f * freq_hz)) - 1.0f;
    uint8_t prescale = (uint8_t)(prescaleval + 0.5f);

    uint8_t oldmode;
    if (pca_read8(PCA9685_MODE1, &oldmode) != HAL_OK) return HAL_ERROR;

    /* Enter sleep to set prescale */
    uint8_t sleepmode = (oldmode & 0x7F) | 0x10; /* set SLEEP bit */
    if (pca_write8(PCA9685_MODE1, sleepmode) != HAL_OK) return HAL_ERROR;

    /* Write prescale */
    if (pca_write8(PCA9685_PRESCALE, prescale) != HAL_OK) return HAL_ERROR;

    /* Restore MODE1 and restart */
    if (pca_write8(PCA9685_MODE1, oldmode) != HAL_OK) return HAL_ERROR;
    HAL_Delay(1); /* allow oscillator to restart */

    uint8_t restart = oldmode | 0x80; /* set RESTART bit */
    return pca_write8(PCA9685_MODE1, restart);
}

/**
 * PCA9685_SetPWM
 *  - Set ON and OFF tick values (0..4095) for the given channel (0..15).
 *  - Returns HAL_OK on success.
 *
 * Note: channel wrap/clamp should be handled by caller.
 */
HAL_StatusTypeDef PCA9685_SetPWM(uint8_t channel, uint16_t on, uint16_t off)
{
    if (!pca_hi2c) return HAL_ERROR;
    if (channel > 15) return HAL_ERROR;

    uint8_t reg = PCA9685_LED0_ON_L + 4 * (channel & 0x0F);
    uint8_t buf[4];

    buf[0] = (uint8_t)(on & 0xFF);
    buf[1] = (uint8_t)((on >> 8) & 0x0F);
    buf[2] = (uint8_t)(off & 0xFF);
    buf[3] = (uint8_t)((off >> 8) & 0x0F);

    /* Write 4 bytes starting at LEDn_ON_L */
    return HAL_I2C_Mem_Write(pca_hi2c, PCA9685_ADDR, reg, I2C_MEMADD_SIZE_8BIT, buf, 4, PCA9685_I2C_TIMEOUT_MS);
}

/**
 * PCA9685_SetPWM_us
 *  - Convenience wrapper: set pulse using microseconds.
 *  - Computes ticks assuming 50 Hz unless you previously set another freq.
 *  - Returns HAL_OK on success, HAL_ERROR if not initialized.
 */
HAL_StatusTypeDef PCA9685_SetPWM_us(uint8_t channel, uint16_t microseconds)
{
    if (!pca_hi2c) return HAL_ERROR;

    /* Default assumption: 50 Hz operation (servo) */
    float freq_hz = 50.0f;

    /* Compute microseconds per tick: (1e6 / freq) / 4096 */
    float tick_us = (1000000.0f / freq_hz) / 4096.0f;
    uint32_t ticks = (uint32_t)((float)microseconds / tick_us);
    if (ticks > 4095U) ticks = 4095U;

    return PCA9685_SetPWM(channel, 0, (uint16_t)ticks);
}