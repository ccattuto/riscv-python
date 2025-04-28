#include <stdio.h>
#include <stdint.h>
#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "semphr.h"
#include "riscvpy.h"

#define NUM_WORKERS 10

SemaphoreHandle_t xMutex;

void worker_task(void *params)
{
    (void) params;
    int id = (int) (uintptr_t) params;
    for (;;) {
        if (xSemaphoreTake(xMutex, portMAX_DELAY)) {
            EMU_LOG_STR_INT("Worker got mutex ", id);
            vTaskDelay(pdMS_TO_TICKS(10 + (id * 5)));  // Hold mutex for a while
            xSemaphoreGive(xMutex);
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

void creator_task(void *params)
{
    (void) params;
    int i;
    for (i = 0; i < NUM_WORKERS; i++) {
        int result = xTaskCreate(worker_task, "Worker", configMINIMAL_STACK_SIZE, (void *)(uintptr_t) i, tskIDLE_PRIORITY + 1, NULL);
        if (result != pdPASS)
            EMU_LOG_STR_INT("Failed to create worker ", i);
        else
            EMU_LOG_STR_XINT("Created worker ", i);
    }
    EMU_LOG_STR("All workers created");

    vTaskDelete(NULL);  // Done
}

void blinker_task(void *params)
{
    (void) params;
    for (;;) {
        EMU_LOG_STR("Blink");
        vTaskDelay(pdMS_TO_TICKS(100));
        EMU_LOG_STR_INT("Free heap space = ", xPortGetFreeHeapSize());
    }
}

int main(void)
{
    xMutex = xSemaphoreCreateMutex();
    xTaskCreate(creator_task, "Creator", configMINIMAL_STACK_SIZE, NULL, tskIDLE_PRIORITY + 2, NULL);
    xTaskCreate(blinker_task, "Blinker", configMINIMAL_STACK_SIZE, NULL, tskIDLE_PRIORITY + 1, NULL);

    vTaskStartScheduler();

    for (;;);
}
