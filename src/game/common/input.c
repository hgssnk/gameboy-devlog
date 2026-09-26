#include "common/input.h"

uint8_t tick;
static uint8_t keys, prev;

void frame(void) {
    vsync();
    prev = keys;
    keys = joypad();
    tick++;
}

uint8_t held(uint8_t key) {
    return keys & key;
}

uint8_t pressed(uint8_t key) {
    return (keys & key) && !(prev & key);
}
