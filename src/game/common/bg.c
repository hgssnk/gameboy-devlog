#include <gb/gb.h>
#include "assets.h"
#include "common/bg.h"

void bg_show(uint8_t index) {
    const Bg *b = &bgs[index];
    uint8_t first = T_PIC_BASE, n = b->n_tiles, k;
    const uint8_t *tiles = b->tiles;

    if (first + n > 128) {                                  // 背景のタイルは、128番の前後で置き場所が分かれる
        k = 128 - first;
        set_bkg_data(first, k, tiles);
        tiles += (uint16_t)k * 16;
        first = 128;
        n -= k;
    }
    set_bkg_data(first, n, tiles);
    set_bkg_tiles(0, 0, PIC_W, PIC_H, b->map);
    fill_bkg_rect(0, PIC_H, 20, 18 - PIC_H, T_BLACK);      // 絵の下は、文の枠の場所
}
