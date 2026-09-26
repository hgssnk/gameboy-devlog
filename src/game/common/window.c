#include <gb/gb.h>
#include "assets.h"
#include "common/window.h"

#define WIN_X 7                         // ウィンドウの左端は、画面の左端より 7 右

void win_open(uint8_t rows) {
    uint8_t x, y;
    for (x = 0; x < 20; x++) {
        set_win_tile_xy(x, 0, T_BLACK);
        for (y = 1; y < rows - 1; y++) set_win_tile_xy(x, y, T_BLANK);
        set_win_tile_xy(x, rows - 1, T_BOTLINE);
    }
    move_win(WIN_X, 144 - rows * 8);
    SHOW_WIN;
}

void win_hide(void) {
    HIDE_WIN;
}

void win_glyph(uint8_t slot, uint8_t g, uint8_t invert) {
    uint8_t buf[16], i;
    const uint8_t *src = &font_tiles[(uint16_t)g * 16];
    for (i = 0; i < 16; i++) buf[i] = invert ? ~src[i] : src[i];
    set_bkg_data(GLYPH_BASE + slot, 1, buf);
}
