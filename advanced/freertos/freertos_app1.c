#include <stdio.h>
#include <stdint.h>
#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "riscvpy.h"

// Task 1: increments a counter
void task1(void *params) {
    (void)params;
    uint32_t counter = 0;

    EMU_LOG_STR("TASK1 starting");

    while (1) {
        EMU_LOG_INT(counter);
        counter++;
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

// Task 2: decrements a counter
void task2(void *params) {
    (void)params;
    uint32_t counter = 0xFFFFFFFF;
    
    EMU_LOG_STR("TASK2 starting");
    while (1) {
        counter -= 1;
        EMU_LOG_INT(counter);
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

int main(void) {
    xTaskCreate(task1, "task1", configMINIMAL_STACK_SIZE, NULL, tskIDLE_PRIORITY + 1, NULL);
    xTaskCreate(task2, "task2", configMINIMAL_STACK_SIZE, NULL, tskIDLE_PRIORITY + 1, NULL);

    // start FreeRTOS
    vTaskStartScheduler();

    // should never get here
    while (1);

    return 0;
}
