/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * STM32F103C8T6 / Blue Pill
  *   - PC13 : on-board LED, active low (low = LED on)
  *   - PA9  : USART1_TX, PA10 : USART1_RX, 115200 8N1
  *   - HSE  : 8 MHz crystal, SYSCLK 72 MHz (PLL x9)
  *
  ******************************************************************************
  */
/* USER CODE END Header */

#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* Private defines -----------------------------------------------------------*/
#define LED_GPIO_Port GPIOC
#define LED_Pin GPIO_PIN_13

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
