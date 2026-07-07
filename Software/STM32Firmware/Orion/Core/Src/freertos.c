/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "pca9685.h"
#include "i2c.h"
#include "LegMotion.h"
#include "BodyIK.h"
#include "imu.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */
extern I2C_HandleTypeDef hi2c1;   // PCA driver is on I2C1
extern I2C_HandleTypeDef hi2c3;   // I2C3 is used for IMU and voltage monitors
extern UART_HandleTypeDef huart2; // HUART1 is used for Jetson, so use HUART2 for debug prints
extern UART_HandleTypeDef huart1; // The UART connected to the Jetson

IMU_OrientationTypeDef current_imu_orientation; // Global variable to hold the latest IMU orientation

// Struct matching the Jetson packet (1 byte type + 36 bytes floats)
// Packed to ensure no padding bytes are added by the compiler, which would break parsing
struct __attribute__((packed)) CmdPayload {
    uint8_t cmd_type;
    float lin_x;
    float lin_y;
    float ang_z;
    float roll;
    float pitch;
    float yaw;
    float z_offset;
    float x_offset;
    float y_offset;
    float pivot_x;
    float pivot_y;
};

#define CMD_NORMAL 0x01
#define CMD_RESET 0x02
#define CMD_WAVE 0x03
#define CMD_HEEL 0x04
#define CMD_DANCE 0x05
#define CMD_EXTRAS 0x06
#define CMD_EYES 0x07

// DMA Buffer and tracking
#define DMA_RX_BUFFER_SIZE 64 // Larger than the expected command size to ensure no bytes are missed
uint8_t dma_rx_buffer[DMA_RX_BUFFER_SIZE]; // Circular Queue for DMA reception of UART data
uint16_t old_pos = 0;

// Parser state machine variables
#define PAYLOAD_SIZE 45
uint8_t payload_buffer[PAYLOAD_SIZE]; // Queue to hold incoming payload bytes
uint8_t payload_index = 0;
int parser_state = 0;

// Parsed command storage
struct CmdPayload last_cmd; // Struct to hold the payload data cleanly
volatile int new_cmd_ready = 0; // Flag to indicate a new command is ready // Not used right now
uint32_t last_cmd_timestamp_ms = 0; // Extra safety to prevent stale commands

// volatile uint32_t checksum_errors = 0;
// volatile uint32_t uart_errors = 0;

/* USER CODE END Variables */
/* Definitions for controlTask */
osThreadId_t controlTaskHandle;
const osThreadAttr_t controlTask_attributes = {
  .name = "controlTask",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityRealtime,
};
/* Definitions for imuTask */
osThreadId_t imuTaskHandle;
const osThreadAttr_t imuTask_attributes = {
  .name = "imuTask",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityHigh,
};
/* Definitions for commTask */
osThreadId_t commTaskHandle;
const osThreadAttr_t commTask_attributes = {
  .name = "commTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for cmdMutex */
osMutexId_t cmdMutexHandle;
const osMutexAttr_t cmdMutex_attributes = {
  .name = "cmdMutex"
};
/* Definitions for imuMutex */
osMutexId_t imuMutexHandle;
const osMutexAttr_t imuMutex_attributes = {
  .name = "imuMutex"
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

void StartControlTask(void *argument);
void StartIMUTask(void *argument);
void StartCommTask(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */
  /* Create the mutex(es) */
  /* creation of cmdMutex */
  cmdMutexHandle = osMutexNew(&cmdMutex_attributes);

  /* creation of imuMutex */
  imuMutexHandle = osMutexNew(&imuMutex_attributes);

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of controlTask */
  controlTaskHandle = osThreadNew(StartControlTask, NULL, &controlTask_attributes);

  /* creation of imuTask */
  imuTaskHandle = osThreadNew(StartIMUTask, NULL, &imuTask_attributes);

  /* creation of commTask */
  commTaskHandle = osThreadNew(StartCommTask, NULL, &commTask_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartControlTask */
/**
  * @brief  Function implementing the controlTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartControlTask */
void StartControlTask(void *argument)
{
  /* USER CODE BEGIN StartControlTask */
  osDelay(2000); // wait peripherals up
  I2C_Scan(&hi2c1, &huart2);
  I2C_Scan(&hi2c3, &huart2);
  PCA9685_Init(&hi2c1, PCA9685_I2C_ADDRESS, 0);
  PCA9685_SetOscillatorFrequency(27000000);
  PCA9685_SetPWMFreq(50.0f);

  LegIK_HardwareInit(); // Init the IK leg structs 
  struct CmdPayload active_cmd = {0}; // Struct to hold the currently active command
  static uint8_t prev_cmd_type = CMD_RESET;

  // OPTIONAL: Explicitly turn off ALL 16 channels at startup so they don't hold old positions
  // for (uint8_t i = 0; i < 16; i++) {
  //     PCA9685_SetPWM(i, 0, 4096); // 4096 turns the pin fully OFF
  // }

  // Center all 12 servos
  // centerAllServos();

  // Variables for body control
  // float pitch = 0.0f;
  // float roll = 0.0f;
  // float yaw = 0.0f;
  // float z_translation = 0.0f;

  // standingPose(); // Drive to neutral pose

  osDelay(2000);

  /* Infinite loop */
  for(;;)
  {
    HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);

    // Safely copy the latest command from the commTask
    osMutexAcquire(cmdMutexHandle, osWaitForever);
    active_cmd = last_cmd;
    osMutexRelease(cmdMutexHandle);

    // If more than 500 milliseconds have passed since the last valid command,
    // stop the robot for safety
    if ((HAL_GetTick() - last_cmd_timestamp_ms) > 500) {
        active_cmd.cmd_type = CMD_RESET;
        active_cmd.lin_x = 0.0f;
        active_cmd.lin_y = 0.0f;
        active_cmd.ang_z = 0.0f;
        active_cmd.roll = 0.0f;
        active_cmd.pitch = 0.0f;
        active_cmd.yaw = 0.0f;
        active_cmd.z_offset = 0.0f;
    }

    // Smooth the target height, tilt, and translation values using an Exponential Moving Average (EMA)
    static float smooth_z = 0.0f;
    static float smooth_roll = 0.0f;
    static float smooth_pitch = 0.0f;
    static float smooth_yaw = 0.0f;
    static float smooth_x_offset = 0.0f;
    static float smooth_y_offset = 0.0f;
    // Filter coefficient (0.0 < alpha <= 1.0)
    // 0.15 at 50Hz gives a smooth transition over ~130ms while remaining responsive
    const float alpha = 0.15f;
    smooth_z        += alpha * (-active_cmd.z_offset - smooth_z); // Jetson sends + to lift body up. Inverse IK matrix requires -z_offset to pull body up.
    smooth_roll     += alpha * (active_cmd.roll - smooth_roll);
    smooth_pitch    += alpha * (active_cmd.pitch - smooth_pitch);
    smooth_yaw      += alpha * (active_cmd.yaw - smooth_yaw);
    smooth_x_offset += alpha * (active_cmd.x_offset - smooth_x_offset);
    smooth_y_offset += alpha * (active_cmd.y_offset - smooth_y_offset);

    // Process Kinematics and Motion state machine based on cmd_type
    switch(active_cmd.cmd_type) 
    {
        case CMD_NORMAL:
            {
                float target_feet[4][3];

                // Calculate raw gait foot trajectory paths relative to default stance
                calculateTrotGaitPositions(active_cmd.lin_x, active_cmd.lin_y, active_cmd.ang_z, target_feet);

                // Stream footprints through orientation matrix to apply Roll/Pitch/Yaw (using smoothed parameters)
                updateBodyPostureWithFeet(target_feet, 0.0f, 0.0f, smooth_z,
                                          smooth_roll, smooth_pitch, smooth_yaw,
                                          active_cmd.pivot_x, active_cmd.pivot_y, 0.0f);
                // Non-smoothing code:
                // // Relative Height Conversion. 
                // // Jetson sends + to lift body up. Inverse IK matrix requires -transZ to pull body up.
                // float transZ = -active_cmd.z_offset; 

                // // Stream footprints through orientation matrix to apply Roll/Pitch/Yaw
                // updateBodyPostureWithFeet(target_feet, 0.0f, 0.0f, transZ,
                //                           active_cmd.roll, active_cmd.pitch, active_cmd.yaw,
                //                           active_cmd.pivot_x, active_cmd.pivot_y, 0.0f);
            }
            break;

        case CMD_EXTRAS:
            {
                // In extras mode, handle relative height translation and body shifts (using smoothed parameters)
                updateBodyPosture(smooth_x_offset, smooth_y_offset, smooth_z,
                                  smooth_roll, smooth_pitch, smooth_yaw,
                                  active_cmd.pivot_x, active_cmd.pivot_y, 0.0f);
            }
            break;

        case CMD_WAVE:
            {
                float target_feet[4][3];
                
                // Tell the function to restart the animation if we JUST switched to wave mode
                bool just_started = (prev_cmd_type != CMD_WAVE);
                
                float shiftX = 0.0f;
                float shiftY = 0.0f;
                float shiftZ = 0.0f;
                float roll = 0.0f;
                float pitch = 0.0f;
                float tibia_angle = -1.0f;
                calculateWavePositions(target_feet, &shiftX, &shiftY, &shiftZ, &roll, &pitch, &tibia_angle, just_started);
                float transZ = 0.0f; // -active_cmd.z_offset // Ignore initial Z offset for wave
                updateBodyPostureWithFeet(target_feet, shiftX, shiftY, transZ + shiftZ,
                                          active_cmd.roll + roll, active_cmd.pitch + pitch, active_cmd.yaw,
                                          0.0f, 0.0f, 0.0f);

                // If Phase 3 is active, override the Tibia servo angle with the waving angle
                if (tibia_angle >= 0.0f) {
                    setServoAngle(CH_FR_TIBIA, tibia_angle);
                }
            }
            break;

        case CMD_HEEL:
            heelingPose();
            break;

        case CMD_DANCE:
            // TODO: Implement dance
            break;

        case CMD_RESET:
        default:
            standingPose(); // Safely return to flat, neutral stance
            break;

        case CMD_EYES:
            break;
    }

    // Update previous command tracker for the next loop iteration
    prev_cmd_type = active_cmd.cmd_type;

    // Clean, structured Debug Print to UART2
    // char debug_msg[128];
    // int n = snprintf(debug_msg, sizeof(debug_msg), 
    //                  "Mode: 0x%02X | X: %d | Y: %d | Yaw: %d | Z_Offset: %dmm\r\n", 
    //                  active_cmd.cmd_type, 
    //                  (int)(active_cmd.lin_x * 100), 
    //                  (int)(active_cmd.lin_y * 100), 
    //                  (int)(active_cmd.yaw * 100),
    //                  (int)(active_cmd.z_offset));
    // HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, (uint16_t)n, 10);

    // static uint32_t last_error_print = 0;
    // if (HAL_GetTick() - last_error_print > 500) {
    //     last_error_print = HAL_GetTick();
    //     char err_msg[64];
    //     int n = snprintf(err_msg, sizeof(err_msg), "CS_Err: %lu | UART_Err: %lu\r\n", checksum_errors, uart_errors);
    //     HAL_UART_Transmit(&huart2, (uint8_t*)err_msg, (uint16_t)n, 10);
    // }

    osDelay(20); // Steady 50Hz control loop cycle execution

    // char msg2[64];
    // int n2 = snprintf(msg2, sizeof(msg2), "Orientation is Y: %d, P: %d, R: %d\r\n", (int)current_imu_orientation.yaw, (int)current_imu_orientation.pitch, (int)current_imu_orientation.roll);
    // HAL_UART_Transmit(&huart2, (uint8_t*)msg2, (uint16_t)n2, PCA9685_I2C_TIMEOUT_MS);

    // ********* Body Update Tests ***********
    // float time = (float)HAL_GetTick() / 1000.0f;
    // // Example: Slowly pitch the front of the body up and down using a sine wave
    // pitch = sinf(time * 5.0f) * 0.2f; 
    // z_translation = -sinf(time * 5.0f) * 20.0f;
    // updateBodyPosture(0.0f, 0.0f, z_translation, roll, pitch, yaw, 0.0f, 0.0f, 0.0f);
    // heelingPose();
    // Example: Yaw the body left and right
    // yaw = sinf(time * 5.0f) * 0.3f;
    // Example: Roll the body left and right
    // roll = sinf(time * 5.0f) * 0.2f;
    // updateBodyPosture(0.0f, 0.0f, z_translation, roll, pitch, yaw, 248.5f/2.0f, -165.2f/2.0f, 0.0f);
    // osDelay(20);
    // waveFrontRightLeg();
    // osDelay(1000);

    // *********** STEPPING TEST ***********
    // sineStepGait();
    // Since the gait commands themselves have interpolation delays,
    // we do not need a big delay here
  }
  /* USER CODE END StartControlTask */
}

/* USER CODE BEGIN Header_StartIMUTask */
/**
* @brief Function implementing the imuTask thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartIMUTask */
void StartIMUTask(void *argument)
{
  /* USER CODE BEGIN StartIMUTask */

  osDelay(2000);
  IMU_Init(&hi2c3, &huart2);
  IMU_OrientationTypeDef imu_orientation; 

  /* Infinite loop */
  for(;;)
  {
    IMU_ReadOrientation(&hi2c3, &imu_orientation);

    osMutexAcquire(imuMutexHandle, osWaitForever);
    current_imu_orientation = imu_orientation;
    osMutexRelease(imuMutexHandle);
    
    osDelay(10); // 100Hz read rate
  }
  /* USER CODE END StartIMUTask */
}

/* USER CODE BEGIN Header_StartCommTask */
/**
* @brief Function implementing the commTask thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartCommTask */
void StartCommTask(void *argument)
{
  /* USER CODE BEGIN StartCommTask */

  // Start continuous DMA reception on USART1 in the background
  HAL_UART_Receive_DMA(&huart1, dma_rx_buffer, DMA_RX_BUFFER_SIZE);

  /* Infinite loop */
  for(;;)
  {
    // Check where the DMA currently is writing.
    // __HAL_DMA_GET_COUNTER returns the number of bytes REMAINING in the buffer before 
    // it wraps around, so subtract from total size to get the current position.
    uint16_t current_pos = DMA_RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(huart1.hdmarx);

    // current_pos is the REAR of the queue where new bytes are being written, 
    // old_pos is the FRONT of the queue where we are reading from.

    // Process all new bytes that have arrived since we last checked
    // (i.e. until our REAR catches up to the FRONT)
    while (old_pos != current_pos) {
        uint8_t rx_byte = dma_rx_buffer[old_pos];

        // State machine to find headers, read payload, and check checksum
        switch(parser_state) {
            
            // Looking for Header 1 (0x55)
            // If 1st header byte was found, set state to 1 to look for 2nd header byte
            case 0:
                if (rx_byte == 0x55) parser_state = 1;
                break;
            
            // Looking for Header 2 (0xAA). 
            // If found, set state to 2 to start reading payload bytes
            // If not found, look for header 1 again
            case 1: 
                if (rx_byte == 0xAA) {
                    parser_state = 2;
                    payload_index = 0;
                } else if (rx_byte != 0x55) {
                    parser_state = 0;
                }
                break;
                
            // Reading Payload (PAYLOAD_SIZE bytes)
            // Once payload is full, verify checksum (state 3)
            case 2:
                payload_buffer[payload_index++] = rx_byte;
                if (payload_index >= PAYLOAD_SIZE) {
                    parser_state = 3;
                }
                break;
            
            // - Verify Checksum (parity)
            // - Safely copy bytes from payload_buffer directly into the last_cmd struct to 
            //   avoid alignment HardFaults. Use mutex to prevent race conditions.
            //   Payload_buffer is just a byte array, no gaurantee of correct alignment for
            //   struct access, so use memcpy which can handle unaligned access.
            // - Set a flag to indicate data is ready for use
            // - Reset state machine for next packet
            case 3: 
                uint8_t received_checksum = rx_byte;
                uint8_t calculated_checksum = 0;   
                for (int i = 0; i < PAYLOAD_SIZE; i++) {
                    calculated_checksum ^= payload_buffer[i];
                }
                if (calculated_checksum == received_checksum) {
                    osMutexAcquire(cmdMutexHandle, osWaitForever);
                    memcpy(&last_cmd, payload_buffer, sizeof(struct CmdPayload));
                    new_cmd_ready = 1;
                    last_cmd_timestamp_ms = HAL_GetTick();
                    osMutexRelease(cmdMutexHandle);
                }else{
                    // checksum_errors++;
                }
                parser_state = 0;
                break;
        }

        // Advance our read pointer, wrapping around if needed
        old_pos = (old_pos + 1) % DMA_RX_BUFFER_SIZE;
    }

    // Let FreeRTOS give CPU time to other tasks
    osDelay(10); // 100Hz command processing rate
  }
  /* USER CODE END StartCommTask */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART1) {
        // uart_errors++;
        
        // Clear overrun and noise flags so DMA reception doesn't lock up
        __HAL_UART_CLEAR_OREFLAG(huart);
        __HAL_UART_CLEAR_NEFLAG(huart);
        __HAL_UART_CLEAR_FEFLAG(huart);
        
        // Restart circular DMA reception
        HAL_UART_Receive_DMA(huart, dma_rx_buffer, DMA_RX_BUFFER_SIZE);
    }
}

/* USER CODE END Application */

