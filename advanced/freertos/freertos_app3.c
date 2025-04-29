#include <stdio.h>
#include <stdint.h>
#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "semphr.h"
#include "riscv-py.h"

#define STORM_WORKER_LIFETIME_MS   10
#define STORM_SPAWN_INTERVAL_MS    100
#define STORM_WORKERS_PER_BURST    10

void storm_worker_task(void *params)
{
    int id = (int)(uintptr_t)params;

    EMU_LOG_STR_INT("Worker started ", id);

    // Simulate some work
    vTaskDelay(pdMS_TO_TICKS(STORM_WORKER_LIFETIME_MS));

    EMU_LOG_STR_INT("Worker finished ", id);

    vTaskDelete(NULL);  // Self-delete
}

void storm_spawner_task(void *params)
{
    (void) params;
    static int next_id = 0;
    for (;;)
    {
        for (int i = 0; i < STORM_WORKERS_PER_BURST; i++)
        {
            BaseType_t result = xTaskCreate(
                storm_worker_task,
                "StormWorker",
                configMINIMAL_STACK_SIZE,
                (void *)(uintptr_t)(next_id++),
                tskIDLE_PRIORITY + 1,
                NULL
            );

            if (result != pdPASS)
            {
                EMU_LOG_STR("Failed to create worker!");
            }
        }

        vTaskDelay(pdMS_TO_TICKS(STORM_SPAWN_INTERVAL_MS));
    }
}

void monitor_task(void *params)
{
    (void) params;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(100));
        EMU_LOG_STR_INT("Free heap space = ", xPortGetFreeHeapSize());
        EMU_LOG_STR_INT("Number of tasks = ", uxTaskGetNumberOfTasks());
    }
}

int main(void)
{
    xTaskCreate(storm_spawner_task, "Spawner", configMINIMAL_STACK_SIZE, NULL, tskIDLE_PRIORITY + 2, NULL);
    xTaskCreate(monitor_task, "Monitor", configMINIMAL_STACK_SIZE, NULL, tskIDLE_PRIORITY + 1, NULL);

    vTaskStartScheduler();

    for (;;);
}
