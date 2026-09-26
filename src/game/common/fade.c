#include <gb/gb.h>
#include "common/fade.h"
#include "common/input.h"

#define PAL_NORMAL 0xE4                 // 背景・スプライトの色（白 薄灰 濃灰 黒）
#define PAL_NOTE 0x24                   // ♪用：黒(3)を白で描く
#define FADE_WAIT 5

// パレットの各色を、lv 段階だけ暗くする
static uint8_t darken(uint8_t pal, uint8_t lv) {
    uint8_t out = 0, i, c;
    for (i = 0; i < 4; i++) {
        c = ((pal >> (i * 2)) & 3) + lv;
        if (c > 3) c = 3;
        out |= c << (i * 2);
    }
    return out;
}

static void apply(uint8_t lv) {
    BGP_REG = darken(PAL_NORMAL, lv);
    OBP0_REG = darken(PAL_NORMAL, lv);
    OBP1_REG = darken(PAL_NOTE, lv);
}

void fade_black(void) {
    apply(3);
}

void fade_out(void) {
    uint8_t lv, i;
    for (lv = 1; lv <= 3; lv++) {
        apply(lv);
        for (i = 0; i < FADE_WAIT; i++) frame();
    }
}

void fade_in(void) {
    uint8_t lv, i;
    for (lv = 3; lv > 0; lv--) {
        apply(lv - 1);
        for (i = 0; i < FADE_WAIT; i++) frame();
    }
}
