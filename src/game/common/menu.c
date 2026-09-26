#include <gb/gb.h>
#include "assets.h"
#include "common/input.h"
#include "common/menu.h"
#include "common/window.h"
#include "vm.h"

#define LABEL_X 3                       // 選択肢の文字の左端のマス
#define ARROW_X 1                       // ▶ のマス

// 条件（フラグ）に合う選択肢だけ出す
static uint8_t visible(const Opt *o) {
    if (o->cond == 1) return flags[o->flag];
    if (o->cond == 2) return !flags[o->flag];
    return 1;
}

uint8_t menu_choose(const Menu *m) {
    const Opt *shown[MAX_OPTS];
    uint8_t n = 0, i, c, sel = 0, last = 0xFF;

    for (i = 0; i < m->n; i++) {
        if (visible(&m->opt[i])) shown[n++] = &m->opt[i];
    }
    if (n == 0) return m->opt[0].target;                    // 出せる選択肢がないときは、先頭へ

    win_open(n + 2);
    for (i = 0; i < m->n_slots; i++) win_glyph(i, m->glyph[i], 0);
    for (i = 0; i < n; i++) {
        for (c = 0; c < COLS; c++) {
            if (shown[i]->cell[c] != 0xFF) set_win_tile_xy(LABEL_X + c, 1 + i, GLYPH_BASE + shown[i]->cell[c]);
        }
    }

    for (;;) {
        if (sel != last) {                                  // ▶ を、選んでいる行へ動かす
            for (i = 0; i < n; i++) set_win_tile_xy(ARROW_X, 1 + i, i == sel ? T_ARROW : T_BLANK);
            last = sel;
        }
        frame();
        if (pressed(J_UP)) sel = sel ? sel - 1 : n - 1;
        else if (pressed(J_DOWN)) sel = (sel + 1) % n;
        else if (pressed(J_A)) return shown[sel]->target;
    }
}
