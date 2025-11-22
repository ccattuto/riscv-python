// LED GPIO peripheral test
// Demonstrates multi-color LED control via memory-mapped I/O

#include <stdio.h>
#include <stdint.h>

#define LED_GPIO_BASE 0x10020000
#define LED_OUT (*(volatile uint32_t *)(LED_GPIO_BASE + 0))

// LED color values (2 bits per LED)
#define LED_OFF   0b00
#define LED_RED   0b01
#define LED_GREEN 0b10
#define LED_BLUE  0b11

// Helper function to set a specific LED color
void set_led(int led_num, int color) {
    // Clear the 2 bits for this LED
    uint32_t mask = ~(0b11 << (led_num * 2));
    LED_OUT = (LED_OUT & mask) | (color << (led_num * 2));
}

// Simple delay loop
void delay(volatile int count) {
    while (count-- > 0);
}

int main(void) {
    printf("LED GPIO Peripheral Test\n");
    printf("Base address: 0x%08X\n\n", LED_GPIO_BASE);

    // Test 1: Turn all LEDs off
    printf("Test 1: All LEDs OFF\n");
    LED_OUT = 0x0000;
    delay(500000);

    // Test 2: Turn all LEDs RED
    printf("Test 2: All LEDs RED\n");
    LED_OUT = 0x5555;  // 01 01 01 01 01 01 01 01 in binary
    delay(500000);

    // Test 3: Turn all LEDs GREEN
    printf("Test 3: All LEDs GREEN\n");
    LED_OUT = 0xAAAA;  // 10 10 10 10 10 10 10 10 in binary
    delay(500000);

    // Test 4: Turn all LEDs BLUE
    printf("Test 4: All LEDs BLUE\n");
    LED_OUT = 0xFFFF;  // 11 11 11 11 11 11 11 11 in binary
    delay(500000);

    // Test 5: Rainbow pattern (each LED different color)
    printf("Test 5: Rainbow pattern\n");
    LED_OUT = 0xE4E4;  // Blue Green Red Off Blue Green Red Off
    delay(500000);

    // Test 6: Walking RED LED
    printf("Test 6: Walking RED LED\n");
    for (int i = 0; i < 8; i++) {
        LED_OUT = 0x0000;
        set_led(i, LED_RED);
        delay(200000);
    }

    // Test 7: Walking BLUE LED (reverse)
    printf("Test 7: Walking BLUE LED (reverse)\n");
    for (int i = 7; i >= 0; i--) {
        LED_OUT = 0x0000;
        set_led(i, LED_BLUE);
        delay(200000);
    }

    // Test 8: Binary counter with color encoding
    printf("Test 8: Binary counter (each bit = RED/OFF)\n");
    for (int i = 0; i < 256; i++) {
        uint32_t pattern = 0;
        for (int bit = 0; bit < 8; bit++) {
            if (i & (1 << bit)) {
                pattern |= (LED_RED << (bit * 2));
            }
        }
        LED_OUT = pattern;
        delay(50000);
    }

    // Test 9: Color cycling on each LED
    printf("Test 9: Color cycling\n");
    int colors[] = {LED_OFF, LED_RED, LED_GREEN, LED_BLUE};
    for (int cycle = 0; cycle < 20; cycle++) {
        for (int color_idx = 0; color_idx < 4; color_idx++) {
            uint32_t pattern = 0;
            for (int led = 0; led < 8; led++) {
                pattern |= (colors[(color_idx + led) % 4] << (led * 2));
            }
            LED_OUT = pattern;
            delay(200000);
        }
    }

    // Test 10: Alternating pattern
    printf("Test 10: Alternating RED/GREEN\n");
    for (int i = 0; i < 10; i++) {
        LED_OUT = 0x5555;  // All RED
        delay(300000);
        LED_OUT = 0xAAAA;  // All GREEN
        delay(300000);
    }

    // Final: Turn all off
    printf("Test complete. Turning all LEDs OFF\n");
    LED_OUT = 0x0000;

    return 0;
}
