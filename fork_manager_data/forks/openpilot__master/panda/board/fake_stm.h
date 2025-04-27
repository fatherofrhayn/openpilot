#if defined(__APPLE__)
#ifndef __API_AVAILABLE
#define __API_AVAILABLE(...)
#endif
#ifndef __API_AVAILABLE_GET_MACRO_93585900
#define __API_AVAILABLE_GET_MACRO_93585900(...)
#endif
#endif

// minimal code to fake a panda for tests
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#include "utils.h"

#define CANFD
#define ALLOW_DEBUG
#define PANDA

#define ENTER_CRITICAL() 0
#define EXIT_CRITICAL() 0

void print(const char *a) {
  printf("%s", a);
}

void puth(unsigned int i) {
  printf("%u", i);
}

typedef struct {
  uint32_t CNT;
} TIM_TypeDef;

TIM_TypeDef timer;
TIM_TypeDef *MICROSECOND_TIMER = &timer;
uint32_t microsecond_timer_get(void);

uint32_t microsecond_timer_get(void) {
  return MICROSECOND_TIMER->CNT;
}

typedef uint32_t GPIO_TypeDef;
