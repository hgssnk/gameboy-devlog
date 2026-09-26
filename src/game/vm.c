#include <gb/gb.h>
#include "assets.h"
#include "common/bg.h"
#include "common/fade.h"
#include "common/input.h"
#include "common/menu.h"
#include "common/text.h"
#include "common/window.h"
#include "vm.h"

uint8_t flags[N_FLAGS];

// 章の終わり：暗転して、章のタイトルを出す
static void end_chapter(void) {
    win_hide();
    fade_out();
    fill_bkg_rect(0, 0, 20, 18, T_BLACK);
    fade_in();
    say_page(&pages[PAGE_END]);
    win_hide();
    fade_out();
}

// 場面を進める（シナリオの命令を、上から順に実行する）
void vm_run(void) {
    uint8_t scene = 0, bg = 0xFF, i, next;
    const uint8_t *p;

    for (i = 0; i < N_FLAGS; i++) flags[i] = 0;

    for (;;) {
        if (scenes[scene].bg != 0xFF && scenes[scene].bg != bg) {   // 背景が変わるときは、暗転する
            bg = scenes[scene].bg;
            win_hide();
            fade_out();
            bg_show(bg);
            fade_in();
        }

        p = scenes[scene].code;
        next = 0xFF;
        while (next == 0xFF) {
            switch (*p++) {
            case OP_PAGE: say_page(&pages[*p++]); break;
            case OP_SET: flags[*p++] = 1; break;
            case OP_MENU: next = menu_choose(&menus[*p++]); break;
            case OP_GOTO: next = *p++; break;
            case OP_SLEEP: end_chapter(); return;
            }
        }
        scene = next;
    }
}
