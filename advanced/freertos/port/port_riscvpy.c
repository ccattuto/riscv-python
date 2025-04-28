#include <stdio.h>
#include <stdint.h>
#include "portmacro_mtime.h"
#include "riscvpy.h"

void vPortSetupTimerInterrupt(void)
{
    EMU_LOG_STR("vPortSetupTimerInterrupt()");

    // initialize mtimecmp <- mtime + 1000
    uint64_t mtime  = read_mtime();
    write_mtimecmp(mtime + 1000);

    // enable MTI
    SET_CSR(mie, 1 << 7);       // MTIE = 1
    SET_CSR(mstatus, 1 << 3);   // MIE = 1
}

void vConfigureTimerForRunTimeStats(void)
{
    EMU_LOG_STR("vConfigureTimerForRunTimeStats()");
}

uint32_t ulGetRunTimeCounterValue(void)
{
    return read_mtime_lo();
}

void vApplicationTickHook(void)
{
    EMU_LOG_STR("TICK");
}

// void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
// {
//     EMU_LOG_STR("Stack overflow detected!");
//     EMU_LOG_INT((uint32_t) xTask);
//     EMU_LOG_STR(pcTaskName);

//     for(;;);  // Hang the system
// }
