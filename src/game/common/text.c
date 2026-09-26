#include <gb/gb.h>
#include "assets.h"
#include "common/input.h"
#include "common/text.h"

#define WIN_X 7                         // ウィンドウの位置（左端は 7）
#define WIN_Y 104                       // 高さ40px = 5マス（上の帯、1行目、すき間、2行目、下の線）
#define GLYPH_BASE 128                  // 文字を入れるタイル番号（背景の絵は 0〜127）
#define TEXT_X 2                        // 本文の左端のマス
#define TYPE_WAIT 2                     // 1文字ごとの待ちフレーム
#define ROW_BAR 0
#define ROW_LINE1 1
#define ROW_LINE2 3
#define ROW_BOTTOM 4
#define CURSOR_X 18

static const uint8_t line_row[2] = { ROW_LINE1, ROW_LINE2 };

// 文字1つを、VRAM の slot 番目のタイルに入れる（invert：白抜き）
static void load_glyph(uint8_t slot, uint8_t g, uint8_t invert) {
    uint8_t buf[16], i;
    const uint8_t *src = &font_tiles[(uint16_t)g * 16];
    for (i = 0; i < 16; i++) buf[i] = invert ? ~src[i] : src[i];
    set_bkg_data(GLYPH_BASE + slot, 1, buf);
}

static void draw_frame(void) {
    uint8_t x;
    for (x = 0; x < 20; x++) {
        set_win_tile_xy(x, ROW_BAR, T_BLACK);
        set_win_tile_xy(x, ROW_LINE1, T_BLANK);
        set_win_tile_xy(x, 2, T_BLANK);
        set_win_tile_xy(x, ROW_LINE2, T_BLANK);
        set_win_tile_xy(x, ROW_BOTTOM, T_BOTLINE);
    }
}

static void show(const Screen *s) {
    uint8_t i, r, c, slot, w, skip = 0, n = s->n_body + s->n_who;

    draw_frame();
    for (i = 0; i < n; i++) load_glyph(i, s->glyph[i], i >= s->n_body);
    for (i = 0; i < 3; i++) {                               // 話す人：上の帯に白抜きで
        if (s->who[i] != 0xFF) set_win_tile_xy(TEXT_X + i, ROW_BAR, GLYPH_BASE + s->who[i]);
    }

    for (r = 0; r < 2; r++) {                               // 文字送り
        for (c = 0; c < 16; c++) {
            slot = s->cell[r][c];
            if (slot == 0xFF) continue;
            set_win_tile_xy(TEXT_X + c, line_row[r], GLYPH_BASE + slot);
            for (w = 0; w < TYPE_WAIT && !skip; w++) {
                frame();
                if (pressed(J_A)) skip = 1;                 // Aで残りを一気に出す
            }
        }
    }

    for (;;) {                                              // 続きの矢印を点滅させて、Aを待つ
        frame();
        set_win_tile_xy(CURSOR_X, ROW_LINE2, (tick & 32) ? T_BLANK : T_CURSOR);
        if (pressed(J_A)) break;
    }
}

void say(const Screen *screens, uint8_t count) {
    uint8_t i;
    draw_frame();
    move_win(WIN_X, WIN_Y);
    SHOW_WIN;
    for (i = 0; i < count; i++) show(&screens[i]);
    HIDE_WIN;
}
