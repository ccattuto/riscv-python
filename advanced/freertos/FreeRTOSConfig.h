#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

// Basic CPU + tick settings
#define configCPU_CLOCK_HZ              ( 1500000UL )   // ~1.5 MHz emulated CPU clock
#define configTICK_RATE_HZ              ( 1000 )        // ~1 ms tick
#define configMAX_PRIORITIES            ( 5 )
#define configMINIMAL_STACK_SIZE        ( 256 )
#define configTOTAL_HEAP_SIZE           ( 32 * 1024 )
#define configMAX_TASK_NAME_LEN         ( 12 )
#define configUSE_16_BIT_TICKS          0

// Memory-mapped timer
#if defined(MTIMER_MMIO) && MTIMER_MMIO == 1
#define configMTIME_BASE_ADDRESS        ( 0x0200BFF8 )
#define configMTIMECMP_BASE_ADDRESS     ( 0x02004000 )
#else
#define configMTIME_BASE_ADDRESS        ( 0 )
#define configMTIMECMP_BASE_ADDRESS     ( 0 )
#endif

// Preemption and hooks
#define configUSE_PREEMPTION            1
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define INCLUDE_vTaskDelay              1
#define INCLUDE_vTaskYield              1
#define INCLUDE_vTaskDelete             1

// Scheduler options
#define configUSE_PORT_OPTIMISED_TASK_SELECTION     0
#define configUSE_TIME_SLICING                      1

// Runtime stats / debug
#define configGENERATE_RUN_TIME_STATS           1
#define configUSE_TRACE_FACILITY                1
#define configUSE_STATS_FORMATTING_FUNCTIONS    0

extern void vConfigureTimerForRunTimeStats(void);
extern uint32_t ulGetRunTimeCounterValue();
#define portCONFIGURE_TIMER_FOR_RUN_TIME_STATS() vConfigureTimerForRunTimeStats()
#define portGET_RUN_TIME_COUNTER_VALUE() ulGetRunTimeCounterValue()

// Mutexes / semaphores / timers
#define configUSE_TIMERS                    1
#define configTIMER_TASK_PRIORITY           (configMAX_PRIORITIES - 1)
#define configTIMER_QUEUE_LENGTH            5
#define configTIMER_TASK_STACK_DEPTH        configMINIMAL_STACK_SIZE

#define configUSE_TASK_NOTIFICATIONS        1  
#define configUSE_MUTEXES                   1
#define configUSE_RECURSIVE_MUTEXES         0
#define configUSE_COUNTING_SEMAPHORES       1

// Optional features
#define configCHECK_FOR_STACK_OVERFLOW      0
#define configUSE_MALLOC_FAILED_HOOK        0
#define configQUEUE_REGISTRY_SIZE           10

// Interrupt settings
#define configKERNEL_INTERRUPT_PRIORITY         ( 0 )
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    ( 0 )

// Assert macro (optional: can log or trap)
#define configASSERT(x) if ((x) == 0) { taskDISABLE_INTERRUPTS(); for( ;; ); }

#endif // FREERTOS_CONFIG_H
