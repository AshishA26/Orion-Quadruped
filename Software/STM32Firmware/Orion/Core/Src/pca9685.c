/**
 * pca9685.c
 *
 * Minimal PCA9685 driver (HAL I2C) 
 * Ported from Adafruit_PWMServoDriver C++ library. (https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library)
 */

#include "pca9685.h"

// Internal State
static I2C_HandleTypeDef *pca_i2c = NULL;
static uint8_t pca_addr = PCA9685_I2C_ADDRESS << 1;
static uint32_t _oscillator_freq = FREQUENCY_OSCILLATOR;

#ifndef min
#define min(a,b) ((a)<(b)?(a):(b))
#endif

// Low Level I2C Write/Read
static uint8_t read8(uint8_t addr) {
    uint8_t buffer;
    HAL_I2C_Mem_Read(pca_i2c, pca_addr, addr, I2C_MEMADD_SIZE_8BIT, &buffer, 1, HAL_MAX_DELAY);
    return buffer;
}

static void write8(uint8_t addr, uint8_t d) {
    HAL_I2C_Mem_Write(pca_i2c, pca_addr, addr, I2C_MEMADD_SIZE_8BIT, &d, 1, HAL_MAX_DELAY);
}

bool PCA9685_Init(I2C_HandleTypeDef *hi2c, uint8_t addr, uint8_t prescale) {
    pca_i2c = hi2c;
    pca_addr = addr << 1; // HAL demands 8-bit shifted address

    // Make sure device is ready
    if (HAL_I2C_IsDeviceReady(pca_i2c, pca_addr, 3, HAL_MAX_DELAY) != HAL_OK) {
        return false;
    }

    PCA9685_Reset();

    // set default internal frequency
    PCA9685_SetOscillatorFrequency(FREQUENCY_OSCILLATOR);

    if (prescale) {
        PCA9685_SetExtClk(prescale);
    } else {
        // set default frequency of 1000
        PCA9685_SetPWMFreq(1000);
    }

    return true;
}

void PCA9685_Reset(void) {
    write8(PCA9685_MODE1, MODE1_RESTART);
    HAL_Delay(10);
}

void PCA9685_Sleep(void) {
    uint8_t awake = read8(PCA9685_MODE1);
    uint8_t sleep = awake | MODE1_SLEEP; // set sleep bit high
    write8(PCA9685_MODE1, sleep);
    HAL_Delay(5); // wait until cycle ends for sleep to be active
}

void PCA9685_Wakeup(void) {
    uint8_t sleep = read8(PCA9685_MODE1);
    uint8_t wakeup = sleep & ~MODE1_SLEEP; // set sleep bit low
    write8(PCA9685_MODE1, wakeup);
}

void PCA9685_SetExtClk(uint8_t prescale) {
    uint8_t oldmode = read8(PCA9685_MODE1);
    uint8_t newmode = (oldmode & ~MODE1_RESTART) | MODE1_SLEEP; // sleep
    write8(PCA9685_MODE1, newmode); // go to sleep, turn off internal oscillator

    // sets both SPLLEEP and EXTCLK bits of the MODE1 register
    write8(PCA9685_MODE1, (newmode |= MODE1_EXTCLK));
    write8(PCA9685_PRESCALE, prescale); // set the prescaler
    HAL_Delay(5);
    
    // clear SLEEP bit to start
    write8(PCA9685_MODE1, (newmode & ~MODE1_SLEEP) | MODE1_RESTART | MODE1_AI);
}

void PCA9685_SetPWMFreq(float freq) {
    if (freq < 1) freq = 1;
    if (freq > 3500) freq = 3500;

    float prescaleval = (((float)_oscillator_freq / (freq * 4096.0f)) + 0.5f) - 1.0f;
    if (prescaleval < PCA9685_PRESCALE_MIN) prescaleval = PCA9685_PRESCALE_MIN;
    if (prescaleval > PCA9685_PRESCALE_MAX) prescaleval = PCA9685_PRESCALE_MAX;
    uint8_t prescale = (uint8_t)prescaleval;

    uint8_t oldmode = read8(PCA9685_MODE1);
    uint8_t newmode = (oldmode & ~MODE1_RESTART) | MODE1_SLEEP; // sleep
    write8(PCA9685_MODE1, newmode); // go to sleep
    write8(PCA9685_PRESCALE, prescale); // set the prescaler
    write8(PCA9685_MODE1, oldmode);
    HAL_Delay(5);
    // turn on auto increment
    write8(PCA9685_MODE1, oldmode | MODE1_RESTART | MODE1_AI);
}

void PCA9685_SetOutputMode(bool totempole) {
    uint8_t oldmode = read8(PCA9685_MODE2);
    uint8_t newmode;
    if (totempole) {
        newmode = oldmode | MODE2_OUTDRV;
    } else {
        newmode = oldmode & ~MODE2_OUTDRV;
    }
    write8(PCA9685_MODE2, newmode);
}

uint8_t PCA9685_ReadPrescale(void) {
    return read8(PCA9685_PRESCALE);
}

uint16_t PCA9685_GetPWM(uint8_t num, bool off) {
    uint8_t reg = PCA9685_LED0_ON_L + 4 * num;
    if (off) reg += 2;
    
    uint8_t buffer[2];
    HAL_I2C_Mem_Read(pca_i2c, pca_addr, reg, I2C_MEMADD_SIZE_8BIT, buffer, 2, HAL_MAX_DELAY);
    return (uint16_t)buffer[0] | ((uint16_t)buffer[1] << 8);
}

uint8_t PCA9685_SetPWM(uint8_t num, uint16_t on, uint16_t off) {
    uint8_t buffer[4];
    buffer[0] = on;
    buffer[1] = on >> 8;
    buffer[2] = off;
    buffer[3] = off >> 8;

    uint8_t reg = PCA9685_LED0_ON_L + 4 * num;
    if (HAL_I2C_Mem_Write(pca_i2c, pca_addr, reg, I2C_MEMADD_SIZE_8BIT, buffer, 4, HAL_MAX_DELAY) == HAL_OK) {
        return 0; // Success
    }
    return 1; // Error
}

void PCA9685_SetPin(uint8_t num, uint16_t val, bool invert) {
    val = min(val, (uint16_t)4095);
    if (invert) {
        if (val == 0) {
            PCA9685_SetPWM(num, 4096, 0);
        } else if (val == 4095) {
            PCA9685_SetPWM(num, 0, 4096);
        } else {
            PCA9685_SetPWM(num, 0, 4095 - val);
        }
    } else {
        if (val == 4095) {
            PCA9685_SetPWM(num, 4096, 0);
        } else if (val == 0) {
            PCA9685_SetPWM(num, 0, 4096);
        } else {
            PCA9685_SetPWM(num, 0, val);
        }
    }
}

void PCA9685_WriteMicroseconds(uint8_t num, uint16_t Microseconds) {
    double pulse = Microseconds;
    double pulselength = 1000000;

    uint16_t prescale = PCA9685_ReadPrescale();

    prescale += 1;
    pulselength *= prescale;
    pulselength /= _oscillator_freq;

    pulse /= pulselength;

    PCA9685_SetPWM(num, 0, pulse);
}

uint32_t PCA9685_GetOscillatorFrequency(void) {
    return _oscillator_freq;
}

void PCA9685_SetOscillatorFrequency(uint32_t freq) {
    _oscillator_freq = freq;
}