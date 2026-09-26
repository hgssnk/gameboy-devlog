#include <gb/gb.h>
#include "assets.h"
#include "common/input.h"
#include "common/text.h"
#include "common/window.h"

#define TEXT_ROWS 4                     // 枠の高さ（上の帯、1行目、2行目、下の線）
#define TEXT_X 2                        // 本文の左端のマス
#define CURSOR_X 18                     // 続きの矢印
#define CURSOR_Y 2
#define TYPE_WAIT 2                     // 1文字ごとの待ちフレーム

void say_page(const Page *p) {
    uint8_t i, r, c, slot, w, skip = 0, n = p->n_body + p->n_who;

    win_open(TEXT_ROWS);
    for (i = 0; i < n; i++) win_glyph(i, p->glyph[i], i >= p->n_body);
    for (i = 0; i < 3; i++) {                               // 話す人：上の帯に、白抜きで
        if (p->who[i] != 0xFF) set_win_tile_xy(TEXT_X + i, 0, GLYPH_BASE + p->who[i]);
    }

    for (r = 0; r < 2; r++) {                               // 文字送り
        for (c = 0; c < COLS; c++) {
            slot = p->cell[r][c];
            if (slot == 0xFF) continue;
            set_win_tile_xy(TEXT_X + c, 1 + r, GLYPH_BASE + slot);
            for (w = 0; w < TYPE_WAIT && !skip; w++) {
                frame();
                if (pressed(J_A)) skip = 1;                 // Aで、残りを一気に出す
            }
        }
    }

    for (;;) {                                              // ▼を点滅させて、Aを待つ
        frame();
        set_win_tile_xy(CURSOR_X, CURSOR_Y, (tick & 32) ? T_BLANK : T_CURSOR);
        if (pressed(J_A)) break;
    }
}
