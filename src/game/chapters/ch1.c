#include <gb/gb.h>
#include "assets.h"
#include "common/fade.h"
#include "common/text.h"
#include "common/walk.h"
#include "chapters/ch1.h"
#include "maps.h"

// 暗転して、マップを切り替える
static void move_to(const Map *map, uint8_t x, uint8_t y, uint8_t face) {
    fade_out();
    walk_enter(map, x, y, face);
    fade_in();
}

// 場面1：部屋（夜）。真っ暗な画面に文だけが出る
static void scene_room(void) {
    uint8_t i;
    walk_hide();
    fill_bkg_rect(0, 0, 20, 18, T_BLACK);
    fade_in();
    SAY(txt_intro1);
    for (i = 0; i < 6; i++) {                                   // 窓の外に、中古屋の看板が灯る
        set_bkg_tile_xy(9 + i % 3, 13 + i / 3, T_SIGN + i);
    }
    SAY(txt_intro2);
}

void ch1_run(void) {
    uint8_t sign_read = 0;

    scene_room();
    move_to(&map_street, 3, 7, FACE_UP);                        // 場面2：夜の街

    for (;;) {
        switch (walk_run()) {
        case ID_VENDING: SAY(txt_vending); break;
        case ID_BOARD: SAY(txt_board); break;
        case ID_VIADUCT: SAY(txt_viaduct); break;
        case ID_SHOPDOOR:
            if (!sign_read) {                                   // 場面3：中古屋の前
                sign_read = 1;
                SAY(txt_sign);
            } else {                                            // 場面4：店内
                move_to(&map_shop, 4, 7, FACE_UP);
            }
            break;
        case ID_OWNER: SAY(txt_owner); break;
        case ID_RADIO: SAY(txt_radio); break;
        case ID_BOX: SAY(txt_todo); break;                      // 場面5（ディグ）は、まだ
        case ID_EXIT:                                           // 何も見つけていないので、出られない
            walk_place(4, 7);
            SAY(txt_notyet);
            break;
        }
    }
}
