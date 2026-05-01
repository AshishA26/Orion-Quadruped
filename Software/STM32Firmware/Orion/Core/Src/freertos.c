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
/* USER CODE END Variables */
/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

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
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN StartDefaultTask */
  /* Infinite loop */
  osDelay(2000); // wait peripherals up
  I2C_Scan(&hi2c1, &huart2);
  I2C_Scan(&hi2c3, &huart2);
  PCA9685_Init(&hi2c1, PCA9685_I2C_ADDRESS, 0);
  PCA9685_SetOscillatorFrequency(27000000);
  PCA9685_SetPWMFreq(50.0f);

  // OPTIONAL: Explicitly turn off ALL 16 channels at startup so they don't hold old positions
  // for (uint8_t i = 0; i < 16; i++) {
  //     PCA9685_SetPWM(i, 0, 4096); // 4096 turns the pin fully OFF
  // }

  // Center all 12 servos
  // centerAllServos();

  // Variables for body control
  float pitch = 0.0f;
  float roll = 0.0f;
  float yaw = 0.0f;
  float z_translation = 0.0f;

  LegIK_HardwareInit(); // Init the IK leg structs 
  // standingPose(); // Drive to neutral pose
  osDelay(2000);

  for(;;)
  {
    HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
    float time = (float)HAL_GetTick() / 1000.0f;

    // Example: Slowly pitch the front of the body up and down using a sine wave
    pitch = sinf(time * 5.0f) * 0.2f; 
    z_translation = -sinf(time * 5.0f) * 20.0f;
    // Example: Yaw the body left and right
    // yaw = sinf(time * 3.0f) * 0.3f;

    // Example: Roll the body left and right
    // roll = sinf(time * 4.0f) * 0.2f;
    
    updateBodyPosture(0.0f, 0.0f, z_translation, roll, pitch, yaw);

    osDelay(20);

    // sineStepGait calculates and steps all legs
    // sineStepGait();
    // Since the gait commands themselves have interpolation delays,
    // we do not need a big delay here
  }
  /* USER CODE END StartDefaultTask */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */

