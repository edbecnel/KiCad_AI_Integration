/**
 * Bedini validation stub — GPIO timing reference for schematic cross-review.
 * Build with Raspberry Pi Pico SDK when integrating a real board.
 */
#include <stdint.h>

#define PICO_GPIO_PIN 15
#define DEAD_TIME_US 2
#define MAX_PWM_HZ 50000

static inline uint32_t dead_time_cycles(void) {
    return (uint32_t)DEAD_TIME_US;
}

void pico_gpio_stub_init(void) {
    /* Configure GPIO15 as optocoupler drive — implementation TBD per board */
}
